import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Play, ShieldCheck, Hexagon, Database, 
  TerminalWindow, CaretRight, ShieldWarning, Key, FileText, ChartLineUp,
  Cpu, IdentificationCard
} from '@phosphor-icons/react';
import { Toaster, toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const Steps = [
  { id: 1, title: 'High-Dimensional Data', icon: FileText },
  { id: 2, title: 'CLOUUD Compression', icon: Cpu },
  { id: 3, title: 'Tokenization Layer', icon: IdentificationCard },
  { id: 4, title: 'Token Verification', icon: ShieldCheck }
];

export default function App() {
  const [view, setView] = useState('playground'); 
  const [currentStep, setCurrentStep] = useState(1);
  const [eventData, setEventData] = useState({
    event_type: "REASONING",
    payload: {
      model: "GPT-5.4",
      reasoning_steps: 10000,
      dataset: "financial_risk_v3",
      decision: "approve_tier_1",
      timestamp: new Date().toISOString()
    }
  });
  const [payloadText, setPayloadText] = useState(JSON.stringify(eventData.payload, null, 2));
  
  const [compressResult, setCompressResult] = useState(null);
  const [tokenResult, setTokenResult] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [apiKey, setApiKey] = useState(null);

  const handleLoadBenchmark = () => {
     const massivePayload = { benchmark: "CLOUUD_1MB_STRESS_TEST", data: [] };
     for(let i=0; i<15000; i++) { 
        massivePayload.data.push({ iter: i, val: Math.random().toString(36).substring(2), state: "active" });
     }
     setEventData({...eventData, event_type: "DATA"});
     const str = JSON.stringify(massivePayload, null, 2);
     setPayloadText(str);
     toast.success(`Loaded ${(str.length / (1024*1024)).toFixed(2)} MB Payload!`);
  };

  const handleCompress = async () => {
    setIsLoading(true);
    try {
      let parsedPayload;
      try { parsedPayload = JSON.parse(payloadText); } 
      catch(e) { toast.error("Invalid JSON payload"); setIsLoading(false); return; }

      const res = await fetch(`${API_URL}/compress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventData.event_type, data: parsedPayload })
      });
      const data = await res.json();
      setCompressResult(data);
      toast.success('Compression & Proof Generated');
      setCurrentStep(2);
    } catch (e) {
      toast.error('Failed to compress data');
    }
    setIsLoading(false);
  };

  const handleTokenize = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/tokenize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          artifact_id: compressResult.artifact_id,
          token_type: eventData.event_type
        })
      });
      const data = await res.json();
      setTokenResult(data);
      toast.success('CLOUUD Data Token Minted!');
      setCurrentStep(3);
    } catch (e) {
      toast.error('Failed to tokenize');
    }
    setIsLoading(false);
  };

  const handleVerify = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/token/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          token_id: tokenResult.token_id, 
          proof_hash: compressResult.proof_hash
        })
      });
      const data = await res.json();
      setVerifyResult(data);
      if(data.valid) {
        toast.success('Token Verified Authentically');
        setCurrentStep(4);
      } else {
        toast.error('Verification Failed');
      }
    } catch (e) {
      toast.error('Verification error');
    }
    setIsLoading(false);
  };

  const generateApiKey = async () => {
    try {
      const res = await fetch(`${API_URL}/api-keys`);
      const data = await res.json();
      setApiKey(data.api_key);
      toast.success('API Key Generated');
    } catch (e) {
      toast.error('Failed to generate key');
    }
  };

  const renderPlayground = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">1. High-Dimensional Input</h2>
                <p className="text-secondary text-sm">Provide massive AI reasoning traces, logs, or datasets.</p>
              </div>
              <button 
                onClick={handleLoadBenchmark}
                className="bg-accent-pink/10 text-accent-pink border border-accent-pink/30 hover:bg-accent-pink/20 px-4 py-2 rounded text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all"
              >
                <ChartLineUp size={16}/> Load 1MB Benchmark
              </button>
            </div>
            
            <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Data Classification</label>
                <select 
                  value={eventData.event_type} 
                  onChange={e => setEventData({...eventData, event_type: e.target.value})}
                  className="w-full bg-background border border-white/10 p-3 rounded text-primary focus:ring-1 focus:ring-accent-cyan outline-none transition-colors font-mono text-sm"
                >
                  <option value="REASONING">REASONING (AI Traces)</option>
                  <option value="DATA">DATA (Large Datasets)</option>
                  <option value="KNOWLEDGE">KNOWLEDGE (Semantic Objects)</option>
                </select>
              </div>
              <div>
                <div className="flex justify-between">
                  <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Raw JSON</label>
                  <span className="text-xs text-muted font-mono">{(payloadText.length / 1024).toFixed(2)} KB</span>
                </div>
                <textarea 
                  rows={8}
                  value={payloadText} 
                  onChange={e => setPayloadText(e.target.value)}
                  className="w-full bg-terminal border border-white/10 p-3 rounded text-accent-cyan focus:ring-1 focus:ring-accent-cyan outline-none transition-colors font-mono text-sm resize-none"
                />
              </div>
              <button 
                onClick={handleCompress}
                disabled={isLoading}
                data-testid="btn-compress"
                className="w-full bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue border border-accent-blue/30 p-3 rounded-md font-bold transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? 'Processing...' : 'Run Compression Engine'} <Cpu weight="bold" />
              </button>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">2. CLOUUD Compression</h2>
            <p className="text-secondary text-sm">Semantic reduction and Zero Knowledge proof generation.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan to-accent-pink opacity-50"></div>
              
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-surface p-4 rounded border border-white/10">
                    <div className="text-muted text-xs uppercase tracking-wider mb-2">Size Reduction</div>
                    <div className="text-accent-green font-bold text-xl">
                      {(compressResult.original_size / 1024).toFixed(2)}KB → {(compressResult.compressed_size / 1024).toFixed(2)}KB
                    </div>
                  </div>
                  <div className="bg-surface p-4 rounded border border-white/10">
                    <div className="text-muted text-xs uppercase tracking-wider mb-2">Compression Ratio</div>
                    <div className="text-accent-cyan font-bold text-xl">
                      {(compressResult.compression_ratio * 100).toFixed(4)}%
                    </div>
                  </div>
                </div>

                <div className="border border-white/10 bg-white/5 p-4 rounded-md flex justify-between items-center">
                  <div>
                    <div className="text-muted text-xs uppercase tracking-[0.2em]">Off-Chain Artifact ID</div>
                    <div className="text-primary mt-1">{compressResult.artifact_id}</div>
                  </div>
                </div>

                <div className="border border-accent-pink/30 bg-accent-pink/5 p-4 rounded-md flex justify-between items-center">
                  <div>
                    <div className="text-accent-pink text-xs uppercase tracking-[0.2em]">Zero Knowledge Proof Hash</div>
                    <div className="text-primary mt-1 truncate max-w-sm">{compressResult.proof_hash}</div>
                  </div>
                </div>

                <button 
                  onClick={handleTokenize}
                  disabled={isLoading}
                  className="w-full bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/50 p-3 rounded-md font-bold hover:bg-accent-yellow/30 transition-all flex justify-center items-center gap-2"
                >
                  <IdentificationCard weight="bold" /> {isLoading ? 'Minting...' : 'Mint Data Token'}
                </button>

              </motion.div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">3. Tokenization Layer</h2>
            <p className="text-secondary text-sm">Creating an identity layer and verifiable reference to the compressed artifact.</p>
            
            <div className="bg-surface border border-accent-yellow/30 p-8 rounded-md flex flex-col items-center relative overflow-hidden">
                <div className="absolute -top-10 -right-10 text-accent-yellow/10">
                   <Hexagon size={200} weight="fill"/>
                </div>

                <IdentificationCard size={64} className="text-accent-yellow mb-4 z-10" />
                <h3 className="text-2xl font-bold text-white z-10 mb-1">{tokenResult.token_id}</h3>
                <div className="text-accent-yellow text-sm font-bold tracking-[0.2em] mb-8 z-10">{tokenResult.token_type} TOKEN</div>

                <div className="w-full bg-terminal rounded p-4 font-mono text-xs space-y-3 z-10 border border-white/10">
                  <div className="flex justify-between border-b border-white/10 pb-2">
                    <span className="text-muted">Original Size:</span>
                    <span className="text-primary">{(tokenResult.original_size_bytes/1024).toFixed(2)} KB</span>
                  </div>
                  <div className="flex justify-between border-b border-white/10 pb-2">
                    <span className="text-muted">Compression:</span>
                    <span className="text-accent-green">{(tokenResult.compression_ratio*100).toFixed(4)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-white/10 pb-2">
                    <span className="text-muted">Artifact Hash:</span>
                    <span className="text-primary truncate w-32 md:w-64 text-right">{tokenResult.artifact_hash}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Metadata URI:</span>
                    <span className="text-accent-cyan">{tokenResult.ipfs_metadata_uri}</span>
                  </div>
                </div>

                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  className="w-full mt-8 bg-accent-green/20 text-accent-green border border-accent-green/50 p-3 rounded-md font-bold hover:bg-accent-green/30 transition-all flex justify-center items-center gap-2 z-10"
                >
                  <ShieldCheck weight="bold" /> {isLoading ? 'Verifying...' : 'Verify Token Integrity'}
                </button>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">4. Token Verification</h2>
             <p className="text-secondary text-sm">Independent verification of the token against the ZK proof hash.</p>

             <div className="bg-terminal border border-white/10 p-6 rounded-md space-y-4">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 p-4 border border-white/10 rounded bg-surface font-mono">
                     <div className="flex items-center gap-3 mb-4">
                        <CheckCircle className="text-accent-green" size={32} weight="fill"/>
                        <div>
                          <div className="text-accent-green font-bold text-lg">VALID TOKEN</div>
                          <div className="text-secondary text-xs">{tokenResult.token_id}</div>
                        </div>
                     </div>
                     <div className="space-y-2 text-sm">
                       <div className="flex justify-between"><span className="text-muted">Compression Verified:</span><span className="text-primary">{verifyResult.compression_verified.toString()}</span></div>
                       <div className="flex justify-between"><span className="text-muted">Artifact Integrity:</span><span className="text-primary">{verifyResult.artifact_integrity.toString()}</span></div>
                       <div className="flex justify-between"><span className="text-muted">Verification Time:</span><span className="text-primary">{verifyResult.verification_time_ms} ms</span></div>
                     </div>
                </motion.div>

                <div className="text-center mt-8 text-white font-bold font-mono tracking-widest text-lg">
                   CLOUUD ARTIFACT ENGINE V1 OPERATIONAL
                 </div>
             </div>
          </div>
        );
      default:
        return null;
    }
  };

  const renderApiDocs = () => {
    return (
      <div className="space-y-8 animate-in fade-in duration-300">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Artifact Engine API</h2>
          <p className="text-secondary">Compress datasets and mint CLOUUD identity tokens programmatically.</p>
        </div>

        <div className="bg-surface border border-white/10 p-6 rounded-md">
          <h3 className="font-bold mb-4 flex items-center gap-2"><Key className="text-accent-yellow"/> Authentication</h3>
          {apiKey ? (
            <div className="bg-terminal p-4 rounded font-mono text-accent-yellow border border-accent-yellow/30 flex justify-between items-center">
              <span>{apiKey}</span>
              <button 
                onClick={() => {navigator.clipboard.writeText(apiKey); toast.success("Copied!");}}
                className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded text-white"
              >
                Copy
              </button>
            </div>
          ) : (
            <button 
              onClick={generateApiKey}
              className="bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/50 hover:bg-accent-yellow/30 px-4 py-2 rounded font-bold transition-all text-sm"
            >
              Generate Secret Key
            </button>
          )}
        </div>

        <div className="space-y-4">
          
          <div className="bg-terminal border border-white/10 rounded-md overflow-hidden">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 text-xs font-mono text-secondary uppercase tracking-widest">
              cURL - 1. Compress Data
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="font-mono text-sm text-primary">
<span className="text-accent-pink">curl</span> -X POST https://api.clouud.dev/v1/compress \<br/>
  -H <span className="text-accent-yellow">"Content-Type: application/json"</span> \<br/>
  -d <span className="text-accent-green">'{'{'}
  "event_type": "DATA",
  "data": {'{'} "massive": "json payload" {'}'}
{'}'}'</span>
              </pre>
            </div>
          </div>

          <div className="bg-terminal border border-white/10 rounded-md overflow-hidden">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 text-xs font-mono text-secondary uppercase tracking-widest">
              cURL - 2. Tokenize Artifact
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="font-mono text-sm text-primary">
<span className="text-accent-pink">curl</span> -X POST https://api.clouud.dev/v1/tokenize \<br/>
  -H <span className="text-accent-yellow">"Content-Type: application/json"</span> \<br/>
  -d <span className="text-accent-green">'{'{'}
  "artifact_id": "YOUR_ARTIFACT_ID",
  "token_type": "REASONING"
{'}'}'</span>
              </pre>
            </div>
          </div>

        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-primary font-sans">
      <Toaster theme="dark" richColors />
      
      <header className="border-b border-white/10 bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="font-mono font-bold text-xl tracking-tighter flex items-center gap-2">
            <Hexagon weight="fill" className="text-accent-cyan" /> CLOUUD.
          </div>
          <div className="flex gap-4">
            <button 
              onClick={() => setView('playground')}
              className={`text-sm font-bold tracking-widest uppercase transition-colors ${view === 'playground' ? 'text-white' : 'text-secondary hover:text-white'}`}
            >
              Artifact Engine
            </button>
            <button 
              onClick={() => setView('api')}
              className={`text-sm font-bold tracking-widest uppercase transition-colors ${view === 'api' ? 'text-accent-yellow' : 'text-secondary hover:text-accent-yellow'}`}
            >
              Developers API
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {view === 'playground' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            <div className="lg:col-span-3 space-y-4">
              <div className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-6">Workflow Sequence</div>
              {Steps.map((step) => {
                const Icon = step.icon;
                const isActive = currentStep === step.id;
                const isPast = currentStep > step.id;
                
                return (
                  <div 
                    key={step.id} 
                    className={`flex items-center gap-4 p-3 rounded-md transition-all ${
                      isActive ? 'bg-surface border border-white/10 shadow-lg' : 
                      isPast ? 'opacity-50' : 'opacity-30'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded flex items-center justify-center ${
                      isActive ? 'bg-accent-cyan/20 text-accent-cyan' : 
                      isPast ? 'bg-accent-green/20 text-accent-green' : 'bg-white/5 text-white/50'
                    }`}>
                      {isPast ? <CheckCircle weight="bold" /> : <Icon weight={isActive ? "fill" : "regular"} />}
                    </div>
                    <span className={`font-bold text-sm ${isActive ? 'text-primary' : 'text-secondary'}`}>
                      {step.title}
                    </span>
                  </div>
                )
              })}
            </div>

            <div className="lg:col-span-9">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {renderPlayground()}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        ) : (
          renderApiDocs()
        )}
      </main>
    </div>
  );
}
