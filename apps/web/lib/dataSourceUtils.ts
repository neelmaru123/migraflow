/**
 * Utility functions for deterministic sorting and formatting of data sources across the UI.
 */

export function sortDataSources<
  T extends {
    name?: string;
    identifier?: string;
    role?: string;
    created_at?: string;
  }
>(dataSources: T[]): T[] {
  if (!Array.isArray(dataSources)) return [];

  return [...dataSources].sort((a, b) => {
    // 1. Role: sources come before destination / target
    const isTargetA = a.role === 'target' || a.role === 'destination' || a.role === 'dest';
    const isTargetB = b.role === 'target' || b.role === 'destination' || b.role === 'dest';
    if (!isTargetA && isTargetB) return -1;
    if (isTargetA && !isTargetB) return 1;

    // Helper: extracts the trailing numeric index (e.g. "src_db_1" -> 1, "Source Database 2" -> 2)
    const getTrailingNumber = (val?: string): number | null => {
      if (!val) return null;
      const matches = val.match(/\d+/g);
      return matches ? parseInt(matches[matches.length - 1], 10) : null;
    };

    // 2. Numeric index from identifier (e.g. "src_src_db_1" vs "src_src_db_2")
    const numFromIdA = getTrailingNumber(a.identifier);
    const numFromIdB = getTrailingNumber(b.identifier);
    if (numFromIdA !== null && numFromIdB !== null && numFromIdA !== numFromIdB) {
      return numFromIdA - numFromIdB;
    }

    // 3. Numeric index from name (e.g. "Source Database 1" vs "Source Database 2")
    const numFromNameA = getTrailingNumber(a.name);
    const numFromNameB = getTrailingNumber(b.name);
    if (numFromNameA !== null && numFromNameB !== null && numFromNameA !== numFromNameB) {
      return numFromNameA - numFromNameB;
    }

    // 4. Natural alphanumeric sort by name
    const nameA = a.name || '';
    const nameB = b.name || '';
    const nameComp = nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' });
    if (nameComp !== 0) return nameComp;

    // 5. Natural alphanumeric sort by identifier
    const idA = a.identifier || '';
    const idB = b.identifier || '';
    const idComp = idA.localeCompare(idB, undefined, { numeric: true, sensitivity: 'base' });
    if (idComp !== 0) return idComp;

    // 6. Fallback to created_at chronological order
    if (a.created_at && b.created_at) {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    }
    return 0;
  });
}
