'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { InitialDataSourceCreate, ValidSourceType } from '../../types/agent';
import {
  ArrowLeft,
  ArrowRight,
  Database,
  HardDrive,
  Server,
  Eye,
  EyeOff,
  Sparkles,
  Key,
  AlertCircle,
  Info,
} from 'lucide-react';
import { ConnectionDetails } from '../../lib/dockerCommandUtils';

interface DatabaseConfigFormProps {
  sourceCount: number;
  onSubmit: (formData: {
    agentName: string;
    agentIdentifier: string;
    sources: InitialDataSourceCreate[];
    destination: InitialDataSourceCreate;
    // Client-side-only connection details (host/port/username/password/database/ssl),
    // keyed by identifier. NEVER sent to the backend API -- only used
    // locally by DockerCommandOutput to fill in the displayed command.
    connectionDetailsByIdentifier: Record<string, ConnectionDetails>;
  }) => void;
  onBack: () => void;
  isSubmitting?: boolean;
  destinationIdentifierError?: string | null;
  onClearDestinationIdentifierError?: () => void;
  existingDestinationIdentifiers?: string[];
}

export const SUPPORTED_ENGINES: {
  type: ValidSourceType;
  name: string;
  category: 'database' | 'file';
  icon: any;
  color: string;
  hex: string;
  border: string;
}[] = [
  {
    type: 'postgresql',
    name: 'PostgreSQL',
    category: 'database',
    icon: Database,
    color: 'bg-sky-400/10 text-sky-400',
    hex: '#38bdf8',
    border: 'border-sky-400/30',
  },
  {
    type: 'mysql',
    name: 'MySQL',
    category: 'database',
    icon: Server,
    color: 'bg-amber-400/10 text-amber-400',
    hex: '#fbbf24',
    border: 'border-amber-400/30',
  },
  {
    type: 'mongodb',
    name: 'MongoDB',
    category: 'database',
    icon: HardDrive,
    color: 'bg-emerald-400/10 text-emerald-400',
    hex: '#34d399',
    border: 'border-emerald-400/30',
  },
];

export const DatabaseConfigForm: React.FC<DatabaseConfigFormProps> = ({
  sourceCount,
  onSubmit,
  onBack,
  isSubmitting = false,
  destinationIdentifierError = null,
  onClearDestinationIdentifierError,
  existingDestinationIdentifiers = [],
}) => {
  const [localDestError, setLocalDestError] = useState<string | null>(null);
  const [hasUserModifiedDestIdentifier, setHasUserModifiedDestIdentifier] = useState(false);
  const [hasAttemptedSubmit, setHasAttemptedSubmit] = useState(false);

  // Only display validation error if the user has actively modified the field, attempted submit, or a server error arrived
  const shouldShowDestError = hasUserModifiedDestIdentifier || hasAttemptedSubmit || Boolean(destinationIdentifierError);
  const activeDestError = shouldShowDestError ? (destinationIdentifierError || localDestError) : null;
  const destIdentifierInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (activeDestError && destIdentifierInputRef.current && (hasUserModifiedDestIdentifier || hasAttemptedSubmit)) {
      destIdentifierInputRef.current.focus();
      destIdentifierInputRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [activeDestError, hasUserModifiedDestIdentifier, hasAttemptedSubmit]);

  const [agentName, setAgentName] = useState('Production Migration Agent');
  const [agentIdentifier, setAgentIdentifier] = useState(
    `agent_${Math.random().toString(36).substring(2, 7)}`
  );

  // Initialize N sources
  const [sources, setSources] = useState<InitialDataSourceCreate[]>(() =>
    Array.from({ length: sourceCount }).map((_, idx) => ({
      name: `Source Database ${idx + 1}`,
      type: idx === 0 ? 'postgresql' : idx === 1 ? 'mysql' : 'mongodb',
      role: 'source',
      identifier: `src_db_${idx + 1}`,
    }))
  );

  // Initialize 1 destination
  const [destination, setDestination] = useState<InitialDataSourceCreate>({
    name: 'Target Destination Database',
    type: 'postgresql',
    role: 'target',
    identifier: 'dst_db_main',
  });

  // Validate destination identifier uniqueness whenever destination, existingDestinationIdentifiers, or sources change,
  // but ONLY if the user has actively modified the field or attempted submission.
  useEffect(() => {
    if (!hasUserModifiedDestIdentifier && !hasAttemptedSubmit) {
      setLocalDestError(null);
      return;
    }

    const trimmed = destination.identifier.toLowerCase().trim();
    if (!trimmed) {
      setLocalDestError(null);
      return;
    }

    const isDuplicateExisting = existingDestinationIdentifiers
      .map((i) => i.toLowerCase().trim())
      .includes(trimmed);

    const isDuplicateSource = sources
      .map((s) => s.identifier.toLowerCase().trim())
      .includes(trimmed);

    if (isDuplicateExisting || isDuplicateSource) {
      setLocalDestError('DB with this identifier already exists');
    } else {
      setLocalDestError(null);
    }
  }, [destination.identifier, existingDestinationIdentifiers, sources, hasUserModifiedDestIdentifier, hasAttemptedSubmit]);

  // Source connection details state: array indexed by source card index 0..N-1
  // Completely immune to identifier renames so values are never lost
  const [sourceConnectionDetails, setSourceConnectionDetails] = useState<ConnectionDetails[]>(() =>
    Array.from({ length: sourceCount }).map((_, idx) => ({
      host: '',
      port: idx === 0 ? '5434' : idx === 1 ? '3307' : '27017',
      username: '',
      password: '',
      database: '',
      ssl: false,
    }))
  );

  // Target destination connection details state: dedicated object
  // Completely immune to destination identifier renames
  const [destinationConnectionDetails, setDestinationConnectionDetails] = useState<ConnectionDetails>({
    host: '',
    port: '5434',
    username: '',
    password: '',
    database: '',
    ssl: false,
  });

  // Password visibility state toggles
  const [showSourcePasswords, setShowSourcePasswords] = useState<Record<number, boolean>>({});
  const [showDestPassword, setShowDestPassword] = useState<boolean>(false);

  // Synchronize when sourceCount changes
  useEffect(() => {
    setSources((prev) => {
      if (prev.length === sourceCount) return prev;
      return Array.from({ length: sourceCount }).map((_, idx) => {
        if (prev[idx]) return prev[idx];
        return {
          name: `Source Database ${idx + 1}`,
          type: idx === 0 ? 'postgresql' : idx === 1 ? 'mysql' : 'mongodb',
          role: 'source',
          identifier: `src_db_${idx + 1}`,
        };
      });
    });

    setSourceConnectionDetails((prev) => {
      if (prev.length === sourceCount) return prev;
      return Array.from({ length: sourceCount }).map((_, idx) => {
        if (prev[idx]) return prev[idx];
        return {
          host: '',
          port: idx === 0 ? '5434' : idx === 1 ? '3307' : '27017',
          username: '',
          password: '',
          database: '',
          ssl: false,
        };
      });
    });
  }, [sourceCount]);

  const handleSourceConnectionDetailChange = (
    index: number,
    field: keyof ConnectionDetails,
    value: string | boolean
  ) => {
    setSourceConnectionDetails((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...(updated[index] || { host: '', port: '', username: '', password: '', database: '', ssl: false }),
        [field]: value,
      };
      return updated;
    });
  };

  const handleDestinationConnectionDetailChange = (
    field: keyof ConnectionDetails,
    value: string | boolean
  ) => {
    setDestinationConnectionDetails((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSourceChange = (
    index: number,
    field: keyof InitialDataSourceCreate,
    value: string
  ) => {
    const updated = [...sources];
    updated[index] = { ...updated[index], [field]: value };
    setSources(updated);
  };

  const handleSourceTypeChange = (index: number, newType: ValidSourceType) => {
    handleSourceChange(index, 'type', newType);
    const defaultPorts: Record<string, string> = { postgresql: '5434', mysql: '3307', mongodb: '27017' };
    const currentPort = sourceConnectionDetails[index]?.port;
    if (!currentPort || ['5432', '5434', '3306', '3307', '27017'].includes(currentPort)) {
      handleSourceConnectionDetailChange(index, 'port', defaultPorts[newType] || '5432');
    }
  };

  const handleDestinationTypeChange = (newType: ValidSourceType) => {
    setDestination((prev) => ({ ...prev, type: newType }));
    const defaultPorts: Record<string, string> = { postgresql: '5434', mysql: '3307', mongodb: '27017' };
    const currentPort = destinationConnectionDetails.port;
    if (!currentPort || ['5432', '5434', '3306', '3307', '27017'].includes(currentPort)) {
      handleDestinationConnectionDetailChange('port', defaultPorts[newType] || '5432');
    }
  };

  const handleDestinationIdentifierChange = (val: string) => {
    const cleanVal = val.toLowerCase().replace(/\s+/g, '_');
    setDestination((prev) => ({ ...prev, identifier: cleanVal }));
    setHasUserModifiedDestIdentifier(true);

    if (onClearDestinationIdentifierError) {
      onClearDestinationIdentifierError();
    }

    const trimmed = cleanVal.trim();
    if (!trimmed) {
      setLocalDestError(null);
      return;
    }

    const isDuplicateExisting = existingDestinationIdentifiers
      .map((i) => i.toLowerCase().trim())
      .includes(trimmed);

    const isDuplicateSource = sources
      .map((s) => s.identifier.toLowerCase().trim())
      .includes(trimmed);

    if (isDuplicateExisting || isDuplicateSource) {
      setLocalDestError('DB with this identifier already exists');
    } else {
      setLocalDestError(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setHasAttemptedSubmit(true);

    const destCleanId = destination.identifier.trim().toLowerCase();

    if (
      existingDestinationIdentifiers &&
      existingDestinationIdentifiers.map((i) => i.toLowerCase().trim()).includes(destCleanId)
    ) {
      setLocalDestError('DB with this identifier already exists');
      destIdentifierInputRef.current?.focus();
      destIdentifierInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    const sourceIds = sources.map((s) => s.identifier.trim().toLowerCase());
    if (sourceIds.includes(destCleanId)) {
      setLocalDestError('DB with this identifier already exists');
      destIdentifierInputRef.current?.focus();
      destIdentifierInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    const connectionDetailsByIdentifier: Record<string, ConnectionDetails> = {};
    sources.forEach((src, idx) => {
      const details = sourceConnectionDetails[idx] || {
        host: '',
        port: '',
        username: '',
        password: '',
        database: '',
        ssl: false,
      };
      connectionDetailsByIdentifier[src.identifier] = details;
      connectionDetailsByIdentifier[src.identifier.toLowerCase().trim()] = details;
    });

    connectionDetailsByIdentifier[destination.identifier] = destinationConnectionDetails;
    connectionDetailsByIdentifier[destination.identifier.toLowerCase().trim()] = destinationConnectionDetails;

    onSubmit({
      agentName: agentName.trim(),
      agentIdentifier: agentIdentifier.trim(),
      sources,
      destination,
      connectionDetailsByIdentifier,
    });
  };

  // Helper to get hex color for a given engine type
  const getEngineHex = (typeStr: string): string => {
    const found = SUPPORTED_ENGINES.find((e) => e.type === typeStr);
    return found ? found.hex : '#38bdf8';
  };

  // Dynamic layout measurement for source cards & SVG pipeline wires
  const sourceCardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const sourcesContainerRef = useRef<HTMLDivElement | null>(null);
  const middleColRef = useRef<HTMLDivElement | null>(null);

  // Default fallback estimate based on current card height with connection fields
  const cardEstimateH = 580;
  const gap = 20;
  const fallbackTotalH = Math.max(380, sources.length * cardEstimateH + Math.max(0, sources.length - 1) * gap);
  const fallbackDestY = Math.round(fallbackTotalH / 2);

  const [measuredLayout, setMeasuredLayout] = useState<{
    startYs: number[];
    destY: number;
    totalH: number;
  } | null>(null);

  const updateLayout = useCallback(() => {
    if (!middleColRef.current || !sourcesContainerRef.current) return;

    const svgRect = middleColRef.current.getBoundingClientRect();
    const sourcesRect = sourcesContainerRef.current.getBoundingClientRect();

    const startYs = sources.map((_, i) => {
      const cardEl = sourceCardRefs.current[i];
      if (cardEl) {
        const cardRect = cardEl.getBoundingClientRect();
        return Math.round(cardRect.top + cardRect.height / 2 - svgRect.top);
      }
      return Math.round(i * (cardEstimateH + gap) + cardEstimateH / 2);
    });

    const measuredTotalH = Math.max(340, Math.round(sourcesRect.height));
    const measuredDestY = Math.round(measuredTotalH / 2);

    setMeasuredLayout((prev) => {
      if (
        prev &&
        prev.totalH === measuredTotalH &&
        prev.destY === measuredDestY &&
        prev.startYs.length === startYs.length &&
        prev.startYs.every((y, idx) => Math.abs(y - startYs[idx]) <= 1)
      ) {
        return prev;
      }
      return { startYs, destY: measuredDestY, totalH: measuredTotalH };
    });
  }, [sources]);

  useEffect(() => {
    updateLayout();

    const frameId = requestAnimationFrame(() => {
      updateLayout();
    });

    if (typeof ResizeObserver !== 'undefined' && sourcesContainerRef.current) {
      const ro = new ResizeObserver(() => {
        updateLayout();
      });
      ro.observe(sourcesContainerRef.current);
      sourceCardRefs.current.forEach((el) => {
        if (el) ro.observe(el);
      });
      return () => {
        cancelAnimationFrame(frameId);
        ro.disconnect();
      };
    } else {
      window.addEventListener('resize', updateLayout);
      return () => {
        cancelAnimationFrame(frameId);
        window.removeEventListener('resize', updateLayout);
      };
    }
  }, [updateLayout]);

  const totalH = measuredLayout?.totalH ?? fallbackTotalH;
  const destY = measuredLayout?.destY ?? fallbackDestY;
  const svgW = 160;
  const mergeX = sources.length === 1 ? svgW : 110;

  // Generate smooth organic wires matching each selected source engine's hex color
  const wires = sources.map((src, i) => {
    const startY =
      measuredLayout?.startYs[i] ?? Math.round(i * (cardEstimateH + gap) + cardEstimateH / 2);
    const hex = getEngineHex(src.type);

    if (sources.length === 1) {
      return {
        id: `form-wire-${i}`,
        d: `M 0 ${startY} L ${svgW} ${destY}`,
        startY,
        hex,
        duration: '1.2s',
        delay: '0s',
      };
    }

    if (Math.abs(startY - destY) < 2) {
      return {
        id: `form-wire-${i}`,
        d: `M 0 ${startY} L ${mergeX} ${destY}`,
        startY,
        hex,
        duration: '1.2s',
        delay: `${i * 0.15}s`,
      };
    }

    const ctrl1X = 45;
    const ctrl1Y = startY;
    const ctrl2X = mergeX - 25;
    const ctrl2Y = destY;

    return {
      id: `form-wire-${i}`,
      d: `M 0 ${startY} C ${ctrl1X} ${ctrl1Y}, ${ctrl2X} ${ctrl2Y}, ${mergeX} ${destY}`,
      startY,
      hex,
      duration: `${1.2 + (i % 3) * 0.2}s`,
      delay: `${i * 0.15}s`,
    };
  });

  const mergedPathD = `M ${mergeX} ${destY} L ${svgW} ${destY}`;
  const destHex = getEngineHex(destination.type);

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-6xl mx-auto space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-none text-[11px] font-mono font-bold uppercase tracking-widest bg-sky-400/10 text-sky-400 border border-sky-400/30">
          STEP 2 OF 3: CONFIGURE ENGINES & AGENT
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl uppercase font-sans">
          Select Source & Destination Engines
        </h2>
        <p className="text-zinc-400 text-xs sm:text-sm max-w-2xl mx-auto leading-relaxed">
          Configure engine details for your {sourceCount} source {sourceCount === 1 ? 'database' : 'databases'}{' '}
          and 1 destination database.
        </p>
      </div>

      {/* Agent Metadata Block */}
      <div className="p-6 rounded-none bg-black border border-zinc-800 backdrop-blur-xl space-y-4 shadow-xl">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Docker Agent Metadata</h3>
          <p className="text-xs text-zinc-400 font-mono">
            Identity details used to register your Docker agent process on the control plane.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-300 mb-1">
              Agent Name
            </label>
            <input
              type="text"
              required
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              placeholder="e.g. Production Migration Agent"
              className="w-full px-4 py-2.5 rounded-none bg-sky-400/[0.04] border border-sky-400/30 text-white text-xs placeholder-zinc-500 focus:outline-none focus:border-sky-400 transition-colors font-sans"
            />
          </div>
          <div>
            <label className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-300 mb-1">
              Unique Agent Identifier
            </label>
            <input
              type="text"
              required
              value={agentIdentifier}
              onChange={(e) => setAgentIdentifier(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
              placeholder="e.g. agent_prod_001"
              className="w-full px-4 py-2.5 rounded-none bg-sky-400/[0.04] border border-sky-400/30 text-sky-400 font-mono text-xs focus:outline-none focus:border-sky-400 transition-colors"
            />
          </div>
        </div>
      </div>

      {/* Prominent Informational Banner */}
      <div className="p-4 bg-sky-950/20 border border-sky-400/30 text-xs font-mono space-y-2 shadow-lg">
        <div className="flex items-center gap-2 text-sky-400 font-bold uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-sky-400 shrink-0" />
          <span>Database Credentials Auto-Fill (Optional)</span>
        </div>
        <p className="text-zinc-300 leading-relaxed text-[11px] font-sans">
          You can provide your database connection credentials (<strong className="text-white font-mono">Host, Port, Username, Password, and Database Name</strong>) directly below to automatically inject them into your generated Docker command.
        </p>
        <div className="flex items-center gap-2 text-[10px] text-amber-300/90 font-mono bg-amber-400/10 px-2.5 py-1.5 border border-amber-400/20">
          <Info className="w-3.5 h-3.5 shrink-0 text-amber-400" />
          <span>
            <strong>Two Options:</strong> Either enter your credentials here for an instant ready-to-run command, OR leave them blank to generate template placeholders and substitute your credentials later in your terminal.
          </span>
        </div>
      </div>

      {/* 3-Column Split Form Layout with Dynamic Engine-Colored Pipeline Wires */}
      <div className="p-6 rounded-none bg-black border border-sky-400/30 space-y-4 shadow-2xl relative overflow-hidden">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px] opacity-5 pointer-events-none" />

        {/* 3-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-0 items-start py-2">
          {/* Left Column: Source Databases Form Cards */}
          <div className="md:col-span-5 flex flex-col justify-start space-y-4">
            <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-zinc-400 mb-2 flex items-center gap-1.5 h-[18px]">
              <span className="w-2 h-2 bg-sky-400 rounded-none inline-block"></span>
              Source Database Engines ({sourceCount})
            </div>

            <div ref={sourcesContainerRef} className="space-y-5">
              {sources.map((source, index) => {
                const currentEngineHex = getEngineHex(source.type);
                const details = sourceConnectionDetails[index] || {
                  host: '',
                  port: '',
                  username: '',
                  password: '',
                  database: '',
                  ssl: false,
                };
                const hasEnteredDetails = Boolean(details.host || details.username || details.password || details.database);

                return (
                  <div
                    ref={(el) => {
                      sourceCardRefs.current[index] = el;
                    }}
                    key={index}
                    className="p-5 rounded-none bg-zinc-950 border border-zinc-800 space-y-4 relative transition-all"
                    style={{ borderColor: `${currentEngineHex}50` }}
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <span
                        className="text-[10px] font-mono font-bold tracking-widest px-2.5 py-0.5 rounded-none uppercase border"
                        style={{
                          backgroundColor: `${currentEngineHex}15`,
                          color: currentEngineHex,
                          borderColor: `${currentEngineHex}40`,
                        }}
                      >
                        SOURCE #{index + 1}
                      </span>
                      <span className="text-[10px] text-zinc-400 font-mono">{source.identifier}</span>
                    </div>

                    {/* Inputs */}
                    <div className="space-y-3">
                      <div>
                        <label className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-1">
                          Source Name
                        </label>
                        <input
                          type="text"
                          required
                          value={source.name}
                          onChange={(e) => handleSourceChange(index, 'name', e.target.value)}
                          placeholder={`Primary DB ${index + 1}`}
                          className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-sans"
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-1">
                          Identifier Tag
                        </label>
                        <input
                          type="text"
                          required
                          value={source.identifier}
                          onChange={(e) =>
                            handleSourceChange(
                              index,
                              'identifier',
                              e.target.value.toLowerCase().replace(/\s+/g, '_')
                            )
                          }
                          className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-sky-400 font-mono text-xs focus:outline-none focus:border-sky-400 transition-colors"
                        />
                      </div>
                    </div>

                    {/* Connection Details Section with Password and Explicit Labels */}
                    <div className="space-y-3 pt-3 border-t border-zinc-900">
                      <div className="flex items-center justify-between">
                        <label className="flex items-center gap-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-300">
                          <Key className="w-3 h-3 text-sky-400" />
                          <span>Credentials</span>
                          <span className="text-[9px] font-normal text-zinc-500 font-sans">(Optional Auto-Fill)</span>
                        </label>
                        {hasEnteredDetails ? (
                          <span className="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 border border-emerald-400/30">
                            Auto-Fill Active
                          </span>
                        ) : (
                          <span className="text-[9px] font-mono text-zinc-500">
                            Leave blank for terminal edit
                          </span>
                        )}
                      </div>

                      {/* Host & Port */}
                      <div className="grid grid-cols-3 gap-2">
                        <div className="col-span-2 space-y-1">
                          <label className="block text-[9px] font-mono uppercase text-zinc-400">
                            Host / IP
                          </label>
                          <input
                            type="text"
                            value={details.host || ''}
                            onChange={(e) => handleSourceConnectionDetailChange(index, 'host', e.target.value)}
                            placeholder="Host or IP (e.g. localhost)"
                            className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-mono"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="block text-[9px] font-mono uppercase text-zinc-400">Port</label>
                          <input
                            type="text"
                            value={details.port || ''}
                            onChange={(e) => handleSourceConnectionDetailChange(index, 'port', e.target.value)}
                            placeholder={source.type === 'mysql' ? '3307' : source.type === 'mongodb' ? '27017' : '5434'}
                            className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-mono"
                          />
                        </div>
                      </div>

                      {/* Username & Password */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="space-y-1">
                          <label className="block text-[9px] font-mono uppercase text-zinc-400">Username</label>
                          <input
                            type="text"
                            value={details.username || ''}
                            onChange={(e) => handleSourceConnectionDetailChange(index, 'username', e.target.value)}
                            placeholder={source.type === 'mysql' || source.type === 'mongodb' ? 'root' : 'postgres'}
                            className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-mono"
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="block text-[9px] font-mono uppercase text-zinc-400">Password</label>
                          <div className="relative">
                            <input
                              type={showSourcePasswords[index] ? 'text' : 'password'}
                              value={details.password || ''}
                              onChange={(e) => handleSourceConnectionDetailChange(index, 'password', e.target.value)}
                              placeholder="Password"
                              className="w-full px-3 py-2 pr-8 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-mono"
                            />
                            <button
                              type="button"
                              onClick={() => setShowSourcePasswords((p) => ({ ...p, [index]: !p[index] }))}
                              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
                              title={showSourcePasswords[index] ? 'Hide password' : 'Show password'}
                            >
                              {showSourcePasswords[index] ? (
                                <EyeOff className="w-3.5 h-3.5 text-zinc-400 hover:text-white" />
                              ) : (
                                <Eye className="w-3.5 h-3.5 text-zinc-400 hover:text-white" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Database Name */}
                      <div className="space-y-1">
                        <label className="block text-[9px] font-mono uppercase text-zinc-400">
                          Database Name <span className="text-zinc-500 font-sans">(appended to connection URL)</span>
                        </label>
                        <input
                          type="text"
                          value={details.database || ''}
                          onChange={(e) => handleSourceConnectionDetailChange(index, 'database', e.target.value)}
                          placeholder={source.type === 'mysql' ? 'e.g. inventory_db' : source.type === 'mongodb' ? 'e.g. analytics_db' : 'e.g. ecommerce_db'}
                          className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-sky-400 transition-colors font-mono"
                        />
                      </div>

                      {/* Require SSL */}
                      <label className="flex items-center gap-2 text-[10px] font-mono text-zinc-400 pt-0.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={details.ssl || false}
                          onChange={(e) => handleSourceConnectionDetailChange(index, 'ssl', e.target.checked)}
                          className="accent-sky-400"
                        />
                        Require SSL Connection
                      </label>
                    </div>

                    {/* Engine Selector Tiles */}
                    <div>
                      <label className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                        Database Engine
                      </label>
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
                        {SUPPORTED_ENGINES.map((engine) => {
                          const EngineIcon = engine.icon;
                          const isSelected = source.type === engine.type;

                          return (
                            <button
                              key={engine.type}
                              type="button"
                              onClick={() => handleSourceTypeChange(index, engine.type)}
                              className={`p-2 rounded-none border flex flex-col items-center gap-1 transition-all ${
                                isSelected
                                  ? `${engine.color} ${engine.border} bg-black shadow-md scale-[1.02]`
                                  : 'bg-black/60 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-white'
                              }`}
                            >
                              <EngineIcon className="w-4 h-4" />
                              <span className="text-[9px] font-semibold uppercase font-mono">{engine.name}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Middle Column: Dynamic Animated Engine-Colored Wires SVG */}
          <div className="hidden md:flex md:col-span-2 flex-col justify-start items-center">
            <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-sky-400 mb-2 h-[18px] flex items-center justify-center animate-pulse">
              Engine Streams
            </div>

            <div ref={middleColRef} style={{ height: `${totalH}px` }} className="w-full relative">
              <svg
                style={{ height: `${totalH}px` }}
                viewBox={`0 0 ${svgW} ${totalH}`}
                className="w-full overflow-visible"
                preserveAspectRatio="none"
              >
                <defs>
                  <filter id="form-neon-glow" x="-30%" y="-30%" width="160%" height="160%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                {/* Layer 1: Dark Track Lines */}
                {wires.map((w) => (
                  <path
                    key={`track-${w.id}`}
                    d={w.d}
                    stroke="#18181b"
                    strokeWidth="4"
                    fill="none"
                  />
                ))}
                {sourceCount > 1 && (
                  <path
                    d={mergedPathD}
                    stroke="#18181b"
                    strokeWidth="5"
                    fill="none"
                  />
                )}

                {/* Layer 2: Dynamic Engine-Colored Laser Lines */}
                {wires.map((w) => (
                  <path
                    key={`laser-${w.id}`}
                    d={w.d}
                    stroke={w.hex}
                    strokeWidth="2.2"
                    fill="none"
                    filter="url(#form-neon-glow)"
                  />
                ))}
                {sourceCount > 1 && (
                  <path
                    d={mergedPathD}
                    stroke={destHex}
                    strokeWidth="3"
                    fill="none"
                    filter="url(#form-neon-glow)"
                  />
                )}

                {/* Layer 3: Anchor Dots & Flowing Particles */}
                {wires.map((w) => (
                  <g key={`particle-${w.id}`}>
                    <circle
                      cx={0}
                      cy={w.startY}
                      r="4.5"
                      fill={w.hex}
                      stroke="#ffffff"
                      strokeWidth="1"
                      filter="url(#form-neon-glow)"
                    />
                    <circle r="3.5" fill="#ffffff" filter="url(#form-neon-glow)">
                      <animateMotion
                        path={w.d}
                        dur={w.duration}
                        begin={w.delay}
                        repeatCount="indefinite"
                      />
                    </circle>
                  </g>
                ))}

                {/* Junction Node */}
                {sourceCount > 1 && (
                  <g transform={`translate(${mergeX}, ${destY})`}>
                    <circle
                      r="5.5"
                      fill="#000000"
                      stroke={destHex}
                      strokeWidth="2"
                      filter="url(#form-neon-glow)"
                    />
                    <circle r="2.5" fill={destHex} className="animate-ping" />
                  </g>
                )}

                {/* Merged Stream Flow Particle */}
                {sourceCount > 1 && (
                  <circle r="4" fill="#ffffff" filter="url(#form-neon-glow)">
                    <animateMotion
                      path={mergedPathD}
                      dur="0.8s"
                      repeatCount="indefinite"
                    />
                  </circle>
                )}

                {/* Destination Target Anchor Dot */}
                <circle
                  cx={svgW}
                  cy={destY}
                  r="5"
                  fill={destHex}
                  stroke="#ffffff"
                  strokeWidth="1"
                  filter="url(#form-neon-glow)"
                />
              </svg>
            </div>
          </div>

          {/* Right Column: Destination Database Form Card */}
          <div className="md:col-span-5 flex flex-col justify-start">
            <div className="text-[10px] font-mono font-bold uppercase tracking-widest text-zinc-400 mb-2 flex items-center gap-1.5 h-[18px]">
              <span className="w-2 h-2 bg-blue-500 rounded-none inline-block"></span>
              Target Destination Sink (1)
            </div>

            <div
              style={{ minHeight: `${totalH}px` }}
              className="p-5 rounded-none bg-zinc-950 border border-blue-500/50 flex flex-col justify-between shadow-[0_0_20px_rgba(59,130,246,0.15)] relative space-y-4"
            >
              <div className="flex items-center justify-between">
                <span
                  className="text-[10px] font-mono font-bold tracking-widest px-2.5 py-0.5 rounded-none uppercase border"
                  style={{
                    backgroundColor: `${destHex}15`,
                    color: destHex,
                    borderColor: `${destHex}40`,
                  }}
                >
                  TARGET SINK
                </span>
                <span className="text-[10px] text-zinc-400 font-mono">{destination.identifier}</span>
              </div>

              <div className="space-y-3 my-1">
                <div>
                  <label className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-1">
                    Destination Name
                  </label>
                  <input
                    type="text"
                    required
                    value={destination.name}
                    onChange={(e) => setDestination({ ...destination, name: e.target.value })}
                    placeholder="Target Data Warehouse"
                    className="w-full px-3 py-2 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-sans"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className={`block text-[10px] font-mono font-semibold uppercase tracking-wider ${
                      activeDestError ? 'text-rose-400' : 'text-zinc-400'
                    }`}>
                      Destination Identifier Tag
                    </label>
                    {activeDestError && (
                      <span className="text-[9px] font-mono text-rose-400 font-semibold uppercase tracking-wider">
                        Conflict Detected
                      </span>
                    )}
                  </div>
                  <input
                    ref={destIdentifierInputRef}
                    id="destination-identifier-input"
                    type="text"
                    required
                    value={destination.identifier}
                    onChange={(e) => handleDestinationIdentifierChange(e.target.value)}
                    className={`w-full px-3 py-2 rounded-none bg-black font-mono text-xs focus:outline-none transition-all ${
                      activeDestError
                        ? 'border-2 border-rose-500 text-rose-300 focus:border-rose-400 bg-rose-950/20 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                        : 'border border-zinc-800 text-blue-400 focus:border-blue-400'
                    }`}
                  />
                  {activeDestError && (
                    <p className="text-[11px] font-mono text-rose-400 mt-1.5 flex items-center gap-1.5 font-medium animate-in fade-in slide-in-from-top-1 duration-150">
                      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
                      <span>{activeDestError}</span>
                    </p>
                  )}
                </div>
              </div>

              {/* Target Connection Details Section with Password and Explicit Labels */}
              <div className="space-y-3 pt-3 border-t border-zinc-900">
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-zinc-300">
                    <Key className="w-3 h-3 text-blue-400" />
                    <span>Target Credentials</span>
                    <span className="text-[9px] font-normal text-zinc-500 font-sans">(Optional Auto-Fill)</span>
                  </label>
                  {Boolean(destinationConnectionDetails.host || destinationConnectionDetails.username || destinationConnectionDetails.password || destinationConnectionDetails.database) ? (
                    <span className="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 border border-emerald-400/30">
                      Auto-Fill Active
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono text-zinc-500">
                      Leave blank for terminal edit
                    </span>
                  )}
                </div>

                {/* Host & Port */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2 space-y-1">
                    <label className="block text-[9px] font-mono uppercase text-zinc-400">
                      Host / IP
                    </label>
                    <input
                      type="text"
                      value={destinationConnectionDetails.host || ''}
                      onChange={(e) => handleDestinationConnectionDetailChange('host', e.target.value)}
                      placeholder="Host or IP (e.g. localhost)"
                      className="w-full px-3 py-1.5 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-[9px] font-mono uppercase text-zinc-400">Port</label>
                    <input
                      type="text"
                      value={destinationConnectionDetails.port || ''}
                      onChange={(e) => handleDestinationConnectionDetailChange('port', e.target.value)}
                      placeholder={destination.type === 'mysql' ? '3307' : destination.type === 'mongodb' ? '27017' : '5434'}
                      className="w-full px-3 py-1.5 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-mono"
                    />
                  </div>
                </div>

                {/* Username & Password */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="block text-[9px] font-mono uppercase text-zinc-400">Username</label>
                    <input
                      type="text"
                      value={destinationConnectionDetails.username || ''}
                      onChange={(e) => handleDestinationConnectionDetailChange('username', e.target.value)}
                      placeholder={destination.type === 'mysql' || destination.type === 'mongodb' ? 'root' : 'postgres'}
                      className="w-full px-3 py-1.5 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-[9px] font-mono uppercase text-zinc-400">Password</label>
                    <div className="relative">
                      <input
                        type={showDestPassword ? 'text' : 'password'}
                        value={destinationConnectionDetails.password || ''}
                        onChange={(e) => handleDestinationConnectionDetailChange('password', e.target.value)}
                        placeholder="Password"
                        className="w-full px-3 py-1.5 pr-8 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => setShowDestPassword((p) => !p)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
                        title={showDestPassword ? 'Hide password' : 'Show password'}
                      >
                        {showDestPassword ? (
                          <EyeOff className="w-3.5 h-3.5 text-zinc-400 hover:text-white" />
                        ) : (
                          <Eye className="w-3.5 h-3.5 text-zinc-400 hover:text-white" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Database Name */}
                <div className="space-y-1">
                  <label className="block text-[9px] font-mono uppercase text-zinc-400">
                    Database Name <span className="text-zinc-500 font-sans">(appended to connection URL)</span>
                  </label>
                  <input
                    type="text"
                    value={destinationConnectionDetails.database || ''}
                    onChange={(e) => handleDestinationConnectionDetailChange('database', e.target.value)}
                    placeholder={destination.type === 'mysql' ? 'e.g. inventory_db' : destination.type === 'mongodb' ? 'e.g. analytics_db' : 'e.g. migration_platform'}
                    className="w-full px-3 py-1.5 rounded-none bg-black border border-zinc-800 text-white text-xs placeholder-zinc-600 focus:outline-none focus:border-blue-400 transition-colors font-mono"
                  />
                </div>

                {/* Require SSL */}
                <label className="flex items-center gap-2 text-[10px] font-mono text-zinc-400 pt-0.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={destinationConnectionDetails.ssl || false}
                    onChange={(e) => handleDestinationConnectionDetailChange('ssl', e.target.checked)}
                    className="accent-blue-400"
                  />
                  Require SSL Connection
                </label>
              </div>

              {/* Engine Selector Tiles for Destination */}
              <div>
                <label className="block text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Destination Database Engine
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
                  {SUPPORTED_ENGINES.map((engine) => {
                    const EngineIcon = engine.icon;
                    const isSelected = destination.type === engine.type;

                    return (
                      <button
                        key={engine.type}
                        type="button"
                        onClick={() => handleDestinationTypeChange(engine.type)}
                        className={`p-2 rounded-none border flex flex-col items-center gap-1 transition-all ${
                          isSelected
                            ? `${engine.color} ${engine.border} bg-black shadow-md scale-[1.02]`
                            : 'bg-black/60 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-white'
                        }`}
                      >
                        <EngineIcon className="w-4 h-4" />
                        <span className="text-[9px] font-semibold uppercase font-mono">{engine.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-3 border-t border-zinc-900 flex items-center justify-between text-[10px] font-mono text-zinc-400">
                <span>Sink Target: {destination.type.toUpperCase()}</span>
                <span style={{ color: destHex }} className="uppercase font-bold">
                  Configured
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 py-3 px-6 rounded-none bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-bold uppercase tracking-wider border border-zinc-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Topology
        </button>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center gap-2 py-3 px-8 rounded-none bg-sky-400 hover:bg-sky-300 text-black text-xs font-bold uppercase tracking-wider transition-colors shadow-lg shadow-sky-950/50 hover:scale-[1.01] disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-none animate-spin"></div>
              <span>Registering Agent...</span>
            </>
          ) : (
            <>
              <span>Generate Docker Command</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export default DatabaseConfigForm;
