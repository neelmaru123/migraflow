// Shared utilities for filling in connection-detail placeholders in
// generated Docker commands. Used by both DockerCommandOutput.tsx (the
// agent-creation flow) and the dashboard's Docker command modal (the
// view/regenerate flow), so they never drift out of sync with each other
// or with the backend's placeholder format.

export interface ConnectionDetails {
  host: string;
  port: string;
  username: string;
  password?: string;
  database: string;
  ssl: boolean;
}

// Mirrors the backend's AgentCommandGenerator._sanitize_identifier exactly
// (apps/api/app/modules/agents/agents_command_generator.py). If this ever
// drifts from the backend's version, placeholder substitution will silently
// fail to match and the raw <..._HOST> style text will still be shown.
export function sanitizeIdentifier(identifier: string): string {
  const cleaned = identifier
    .trim()
    .replace(/[^A-Za-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase();
  return cleaned || 'DB';
}

// Mirrors the backend's used_prefixes collision-avoidance loop exactly, so
// that if two identifiers sanitize to the same base string, the second one
// gets the same "_2", "_3", ... suffix the backend would have generated.
export function resolvePrefix(baseClean: string, rolePrefix: 'SRC' | 'DEST', usedPrefixes: Set<string>): string {
  const base = `${rolePrefix}_${baseClean}`;
  let prefix = base;
  let counter = 2;
  while (usedPrefixes.has(prefix)) {
    prefix = `${base}_${counter}`;
    counter += 1;
  }
  usedPrefixes.add(prefix);
  return prefix;
}

// Substitutes <PREFIX_HOST>, <PREFIX_PORT>, <PREFIX_USER>, <PREFIX_PASSWORD>, <PREFIX_NAME>
// placeholders in the raw command text with real values from connectionDetailsByIdentifier.
// If any parameter is left blank, its placeholder remains intact for manual replacement in the shell.
export function substituteConnectionPlaceholders(
  rawText: string,
  sources: { identifier: string }[],
  destination: { identifier: string } | null | undefined,
  connectionDetailsByIdentifier: Record<string, ConnectionDetails>
): string {
  if (!rawText) return rawText;
  let result = rawText;
  const usedPrefixes = new Set<string>();

  const getDetails = (identifier: string): ConnectionDetails | undefined => {
    if (!identifier) return undefined;
    return (
      connectionDetailsByIdentifier[identifier] ||
      connectionDetailsByIdentifier[identifier.toLowerCase().trim()] ||
      connectionDetailsByIdentifier[identifier.toUpperCase().trim()] ||
      connectionDetailsByIdentifier[sanitizeIdentifier(identifier)]
    );
  };

  const applyForIdentifier = (identifier: string, rolePrefix: 'SRC' | 'DEST') => {
    const details = getDetails(identifier);
    const cleanId = sanitizeIdentifier(identifier);
    const prefix = resolvePrefix(cleanId, rolePrefix, usedPrefixes);
    if (!details) return;

    if (details.host) {
      result = result.split(`<${prefix}_HOST>`).join(details.host);
    }
    if (details.port) {
      result = result.split(`<${prefix}_PORT>`).join(details.port);
    }
    if (details.username) {
      result = result.split(`<${prefix}_USER>`).join(details.username);
    }
    if (details.password) {
      result = result.split(`<${prefix}_PASSWORD>`).join(details.password);
    }
    if (details.database) {
      let dbVal = details.database;
      if (details.ssl) {
        const lineWithPlaceholder = result.split('\n').find((l) => l.includes(`<${prefix}_NAME>`)) || '';
        if (lineWithPlaceholder.includes('postgresql://') || lineWithPlaceholder.includes('postgres://')) {
          dbVal = `${details.database}?sslmode=require`;
        } else if (lineWithPlaceholder.includes('mysql')) {
          dbVal = `${details.database}?ssl=true`;
        } else if (lineWithPlaceholder.includes('mongodb://') || lineWithPlaceholder.includes('mongodb+srv://')) {
          if (result.includes(`<${prefix}_NAME>?authSource=admin`)) {
            result = result.split(`<${prefix}_NAME>?authSource=admin`).join(`${details.database}?authSource=admin&tls=true`);
          } else {
            dbVal = `${details.database}?tls=true`;
          }
        }
      }
      result = result.split(`<${prefix}_NAME>`).join(dbVal);
    }

    // Convenience alias replacements for single destination
    if (rolePrefix === 'DEST') {
      if (details.host) result = result.split(`<DEST_DB_HOST>`).join(details.host);
      if (details.port) result = result.split(`<DEST_DB_PORT>`).join(details.port);
      if (details.username) result = result.split(`<DEST_DB_USER>`).join(details.username);
      if (details.password) result = result.split(`<DEST_DB_PASSWORD>`).join(details.password);
      if (details.database) {
        let destDbVal = details.database;
        if (details.ssl) {
          const destLineWithPlaceholder = result.split('\n').find((l) => l.includes(`<DEST_DB_NAME>`)) || '';
          if (destLineWithPlaceholder.includes('postgresql://') || destLineWithPlaceholder.includes('postgres://')) {
            destDbVal = `${details.database}?sslmode=require`;
          } else if (destLineWithPlaceholder.includes('mysql')) {
            destDbVal = `${details.database}?ssl=true`;
          } else if (destLineWithPlaceholder.includes('mongodb://') || destLineWithPlaceholder.includes('mongodb+srv://')) {
            if (result.includes(`<DEST_DB_NAME>?authSource=admin`)) {
              result = result.split(`<DEST_DB_NAME>?authSource=admin`).join(`${details.database}?authSource=admin&tls=true`);
            } else {
              destDbVal = `${details.database}?tls=true`;
            }
          }
        }
        result = result.split(`<DEST_DB_NAME>`).join(destDbVal);
      }
    }
  };

  sources.forEach((s) => applyForIdentifier(s.identifier, 'SRC'));
  if (destination) applyForIdentifier(destination.identifier, 'DEST');

  // Single-source convenience alias replacements
  if (sources.length === 1) {
    const firstDetails = getDetails(sources[0].identifier);
    if (firstDetails) {
      if (firstDetails.host) result = result.split(`<SOURCE_DB_HOST>`).join(firstDetails.host);
      if (firstDetails.port) result = result.split(`<SOURCE_DB_PORT>`).join(firstDetails.port);
      if (firstDetails.username) result = result.split(`<SOURCE_DB_USER>`).join(firstDetails.username);
      if (firstDetails.password) result = result.split(`<SOURCE_DB_PASSWORD>`).join(firstDetails.password);
      if (firstDetails.database) result = result.split(`<SOURCE_DB_NAME>`).join(firstDetails.database);
    }
  }

  // Dynamic host adaptation: If user is accessing the web console from a public IP / domain (e.g. EC2 or staging domain),
  // and the generated command contains the local fallback "http://host.docker.internal:8000" or "localhost",
  // dynamically replace it with the accessible public endpoint so remote agents connect cleanly.
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1';
    if (!isLocal) {
      const publicBackend =
        window.location.protocol === 'https:'
          ? `${window.location.origin}`
          : `${window.location.protocol}//${host}:8000`;
      result = result.split('BACKEND_URL="http://host.docker.internal:8000"').join(`BACKEND_URL="${publicBackend}"`);
      result = result.split('BACKEND_URL="http://localhost:8000"').join(`BACKEND_URL="${publicBackend}"`);
      result = result.split('BACKEND_URL=http://host.docker.internal:8000').join(`BACKEND_URL=${publicBackend}`);
      result = result.split('BACKEND_URL=http://localhost:8000').join(`BACKEND_URL=${publicBackend}`);
    }
  }

  return result;
}
