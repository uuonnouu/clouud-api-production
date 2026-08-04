import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Play, ShieldCheck, Hexagon, Database, 
  ShieldWarning, FileText, Cpu, Key, IdentificationCard
} from '@phosphor-icons/react';
import { Toaster, toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const Steps = [
  { id: 1, title: 'JSON Event Input', icon: FileText },
  { id: 2, title: 'Compression & Proof', icon: Cpu },
  { id: 3, title: 'Token Minting', icon: IdentificationCard },
  { id: 4, title: 'Verification', icon: ShieldCheck },
  { id: 5, title: 'Tamper Test', icon: ShieldWarning }
];

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [eventData, setEventData] = useState({
    user_id: "user-001",
    package_id: "starter-100",
    amount: 100
  });
  const [payloadText, setPayloadText] = useState(JSON.stringify(eventData, null, 2));
  
  const [eventId, setEventId] = useState(null);
  const [proofData, setProofData] = useState(null);
  const [tokenData, setTokenData] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  const [tamperVerifyResult, setTamperVerifyResult] = useState(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [apiKey, setApiKey] = useState("");

  const getHeaders = () => {
    return {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    };
  };

  const handleGenerateKey = async () => {
    try {
      const res = await fetch(`${API_URL}/api-keys`);
      const data = await res.json();
      setApiKey(data.api_key);
      toast.success('API Key generated successfully');
    } catch (e) {
      toast.error('Failed to generate API Key');
    }
  };

  const handleCreateEvent = async () => {
    if (!apiKey) { toast.error("Please generate an API Key first."); return; }
    setIsLoading(true);
    try {
      let parsedPayload;
      try { parsedPayload = JSON.parse(payloadText); } 
      catch(e) { toast.error("Invalid JSON payload"); setIsLoading(false); return; }

      const res = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ event_type: "transaction", payload: parsedPayload })
      });
      if (res.status === 401 || res.status === 403) throw new Error("Unauthorized: Invalid API Key");
      
      const data = await res.json();
      setEventId(data.event_id);
      toast.success('Event Stored Securely');
      setCurrentStep(2);
    } catch (e) {
      toast.error(e.message || 'Failed to ingest event');
    }
    setIsLoading(false);
  };

  const handleGenerateProof = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/proof`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ event_id: eventId })
      });
      if (!res.ok) throw new Error("Failed to generate proof");
      const data = await res.json();
      setProofData(data);
      toast.success('CLOUUD Proof Generated');
      setCurrentStep(3);
    } catch (e) {
      toast.error(e.message);
    }
    setIsLoading(false);
  };

  const handleTokenize = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/tokenize`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ event_id: eventId })
      });
      if (!res.ok) throw new Error("Failed to mint token");
      const data = await res.json();
      setTokenData(data);
      toast.success('CLOUUD Token Minted!');
      setCurrentStep(4);
    } catch (e) {
      toast.error(e.message);
    }
    setIsLoading(false);
  };

  const handleVerify = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }, // Public endpoint
        body: JSON.stringify({ 
          event_id: eventId, 
          proof: proofData.proof
        })
      });
      const data = await res.json();
      setVerifyResult(data);
      if(data.valid) {
        toast.success('Integrity Verified');
        setCurrentStep(5);
      } else {
        toast.error('Verification Failed');
      }
    } catch (e) {
      toast.error('Verification error');
    }
    setIsLoading(false);
  };

  const handleTamper = async () => {
    setIsLoading(true);
    try {
      let tampered = JSON.parse(payloadText);
      if (tampered.amount) tampered.amount = 9999;
      else tampered.tampered = true;
      
      await fetch(`${API_URL}/tamper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }, // Testing endpoint
        body: JSON.stringify({ event_id: eventId, tampered_payload: tampered })
      });
      toast.warning('Database Payload Tampered!');
      
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, proof: proofData.proof })
      });
      const data = await res.json();
      setTamperVerifyResult(data);
      if(!data.valid) toast.success('Tamper Successfully Detected!');
    } catch (e) {
      toast.error('Error during tamper test');
    }
    setIsLoading(false);
  };

  const renderPlayground = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">1. Authenticated Ingestion</h2>
            <p className="text-secondary text-sm">Create a data event securely with an API Key.</p>
            
            <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">X-API-Key</label>
                  <input 
                    type="text" 
                    value={apiKey} 
                    onChange={e => setApiKey(e.target.value)}
                    placeholder="Generate or paste key"
                    className="w-full bg-background border border-white/10 p-3 rounded text-accent-yellow font-mono text-sm outline-none"
                  />
                </div>
                <button 
                  onClick={handleGenerateKey}
                  className="bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30 px-4 py-3 rounded hover:bg-accent-yellow/20 font-bold transition-all whitespace-nowrap"
                >
                  Generate Key
                </button>
              </div>

              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Transaction Payload (JSON)</label>
                <textarea 
                  rows={6}
                  value={payloadText} 
                  onChange={e => setPayloadText(e.target.value)}
                  className="w-full bg-terminal border border-white/10 p-3 rounded text-accent-cyan font-mono text-sm resize-none outline-none"
                />
              </div>
              <button 
                onClick={handleCreateEvent}
                disabled={isLoading}
                className="w-full bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue border border-accent-blue/30 p-3 rounded-md font-bold transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? 'Storing...' : 'Secure Store Event'} <Play weight="fill" />
              </button>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">2. Compression & Proof</h2>
            <p className="text-secondary text-sm">Deterministic state normalization requiring API Key access.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative">
              {!proofData ? (
                 <button 
                  onClick={handleGenerateProof}
                  disabled={isLoading}
                  className="bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all w-full mt-4 flex justify-center items-center gap-2"
                >
                  <Cpu weight="bold" /> {isLoading ? 'Generating Proof...' : 'Run Local Proof Engine'}
                </button>
              ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                  <div>
                    <h3 className="text-accent-pink uppercase tracking-[0.2em] text-xs font-bold mb-2">Normalized States</h3>
                    {proofData.states.map((s, i) => (
                      <div key={i} className="text-secondary mb-1 border-l-2 border-accent-pink/50 pl-3 break-all">
                        [{i}] {s}
                      </div>
                    ))}
                  </div>

                  <div className="border border-white/10 bg-white/5 p-4 rounded-md">
                    <div className="text-muted text-xs uppercase tracking-[0.2em] mb-1">Merkle Root</div>
                    <div className="text-primary truncate text-accent-pink">{proofData.merkle_root}</div>
                  </div>

                  <button 
                    onClick={() => setCurrentStep(3)}
                    className="w-full bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/50 p-3 rounded-md font-bold hover:bg-accent-yellow/30 transition-all flex justify-center items-center gap-2"
                  >
                    Proceed to Tokenization
                  </button>
                </motion.div>
              )}
            </div>
          </div>
        );
      case 3:
         return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">3. Token Minting</h2>
            <p className="text-secondary text-sm">Abstract verified proofs into local CLOUUD Data Tokens.</p>

            <div className="bg-surface border border-white/10 p-6 rounded-md">
              {!tokenData ? (
                 <button 
                  onClick={handleTokenize}
                  disabled={isLoading}
                  className="bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50 hover:bg-accent-cyan/30 p-3 rounded-md font-bold transition-all w-full flex justify-center items-center gap-2"
                >
                  <IdentificationCard weight="bold" /> {isLoading ? 'Minting...' : 'Mint Data Token'}
                </button>
              ) : (
                 <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-6">
                    <IdentificationCard size={64} className="mx-auto text-accent-cyan mb-4" />
                    <h3 className="text-2xl font-bold text-white mb-2">{tokenData.token_id}</h3>
                    <div className="text-accent-cyan font-mono text-sm tracking-widest mb-6">CLOUUD DATA TOKEN</div>
                    
                    <button 
                      onClick={() => setCurrentStep(4)}
                      className="w-full bg-white/10 hover:bg-white/20 text-white p-3 rounded-md font-bold transition-all"
                    >
                      Proceed to Verification
                    </button>
                 </motion.div>
              )}
            </div>
          </div>
         );
      case 4:
        return (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold tracking-tight text-white mb-2">4. Public Verification</h2>
             <p className="text-secondary text-sm">Independent recalculation of state hashes (No API Key Required).</p>

             <div className="bg-terminal border border-white/10 p-6 rounded-md">
                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  className="w-full bg-accent-green/20 text-accent-green border border-accent-green/50 hover:bg-accent-green/30 p-3 rounded-md font-bold transition-all flex justify-center items-center gap-2"
                >
                  <ShieldCheck weight="bold" /> {isLoading ? 'Verifying...' : 'Verify Data Integrity'}
                </button>

                {verifyResult && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 p-4 border border-white/10 rounded bg-surface font-mono">
                     <div className="flex items-center gap-3 mb-4">
                        <CheckCircle className="text-accent-green" size={32} weight="fill"/>
                        <div>
                          <div className="text-accent-green font-bold text-lg">INTEGRITY VERIFIED</div>
                          <div className="text-secondary text-xs">Root hashes match perfectly.</div>
                        </div>
                     </div>
                     <button 
                      onClick={() => setCurrentStep(5)}
                      className="mt-4 w-full bg-white/10 hover:bg-white/20 text-white p-2 rounded transition-all"
                     >
                        Run Tamper Test
                     </button>
                  </motion.div>
                )}
             </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2">5. Tamper Test</h2>
            <p className="text-secondary text-sm">Simulate a database breach by modifying the payload directly.</p>

            <div className="bg-surface border border-accent-pink/30 p-6 rounded-md">
              <button 
                onClick={handleTamper}
                disabled={isLoading}
                className="w-full bg-accent-pink/20 text-accent-pink border border-accent-pink/50 hover:bg-accent-pink/30 p-3 rounded-md font-bold transition-all mb-4"
              >
                {isLoading ? 'Running...' : 'Modify Payload & Verify'}
              </button>

              {tamperVerifyResult && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-terminal p-4 rounded border border-white/10 font-mono">
                    <div className="flex items-center gap-2 mb-4 text-accent-pink font-bold text-lg">
                        <ShieldWarning size={28} weight="fill"/>
                        TAMPER DETECTED
                    </div>
                </motion.div>
              )}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background text-primary font-sans">
      <Toaster theme="dark" richColors />
      
      <header className="border-b border-white/10 bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="font-mono font-bold text-xl tracking-tighter flex items-center gap-2">
            <Hexagon weight="fill" className="text-accent-cyan" /> CLOUUD.
          </div>
          <span className="text-xs font-bold tracking-widest uppercase text-secondary border border-white/10 px-2 py-1 rounded bg-white/5">
            Production Ready Core
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-3 space-y-4">
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-muted mb-6">E2E Pipeline</div>
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
      </main>
    </div>
  );
}
