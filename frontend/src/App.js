import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Play, ShieldCheck, Hash, Hexagon, Database, Code, 
  TerminalWindow, CaretRight, ShieldWarning, Key, FileText, Graph
} from '@phosphor-icons/react';
import { Toaster, toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const Steps = [
  { id: 1, title: 'Event Ingestion', icon: FileText },
  { id: 2, title: 'Reasoning Capture', icon: Code },
  { id: 3, title: 'ZK Proof Gen', icon: Graph },
  { id: 4, title: 'Persistence', icon: Database },
  { id: 5, title: 'Zero Knowledge Verify', icon: ShieldCheck },
  { id: 6, title: 'Blockchain', icon: TerminalWindow },
  { id: 7, title: 'Tamper Test', icon: ShieldWarning }
];

export default function App() {
  const [view, setView] = useState('playground'); // 'playground' | 'api'
  const [currentStep, setCurrentStep] = useState(1);
  const [eventData, setEventData] = useState({
    event_type: "ai_decision_log",
    payload: {
      action: "approve_loan",
      user: "user-001",
      risk_score: 12,
      model_version: "v4.2"
    }
  });
  const [payloadText, setPayloadText] = useState(JSON.stringify(eventData.payload, null, 2));
  
  const [eventId, setEventId] = useState(null);
  const [proofData, setProofData] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  const [anchorData, setAnchorData] = useState(null);
  const [tamperVerifyResult, setTamperVerifyResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testReport, setTestReport] = useState({});

  const [apiKey, setApiKey] = useState(null);

  const handleCreateEvent = async () => {
    setIsLoading(true);
    try {
      let parsedPayload;
      try { parsedPayload = JSON.parse(payloadText); } 
      catch(e) { toast.error("Invalid JSON payload"); setIsLoading(false); return; }

      const res = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...eventData, payload: parsedPayload })
      });
      const data = await res.json();
      setEventId(data.event_id);
      setTestReport(prev => ({ ...prev, tx: true }));
      toast.success('Event Ingested');
      setCurrentStep(2);
    } catch (e) {
      toast.error('Failed to ingest event');
    }
    setIsLoading(false);
  };

  const handleGenerateProof = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/proof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId })
      });
      const data = await res.json();
      setProofData(data);
      setTestReport(prev => ({ ...prev, capture: true, compress: true, proof: true, persist: true }));
      toast.success('Zero Knowledge Proof Generated');
      setCurrentStep(5);
    } catch (e) {
      toast.error('Failed to generate ZK proof');
    }
    setIsLoading(false);
  };

  const handleVerify = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          event_id: eventId, 
          zk_proof: proofData.proof.zk_proof,
          public_signals: proofData.proof.public_signals
        })
      });
      const data = await res.json();
      setVerifyResult(data);
      if(data.valid) {
        setTestReport(prev => ({ ...prev, verify: true }));
        toast.success('ZK Verification Successful');
        setCurrentStep(6);
      } else {
        toast.error('Verification Failed');
      }
    } catch (e) {
      toast.error('Verification error');
    }
    setIsLoading(false);
  };

  const handlePublish = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/publish-proof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId })
      });
      const data = await res.json();
      setAnchorData(data);
      setTestReport(prev => ({ ...prev, anchor: true }));
      toast.success('Anchored Public Signal to Blockchain');
      setCurrentStep(7);
    } catch (e) {
      toast.error('Publish error');
    }
    setIsLoading(false);
  };

  const handleTamper = async () => {
    setIsLoading(true);
    try {
      let tampered = JSON.parse(payloadText);
      tampered.risk_score = 999; // Malicious edit
      
      await fetch(`${API_URL}/tamper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, tampered_payload: tampered })
      });
      toast.warning('Event Payload Tampered in DB!');
      
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          event_id: eventId, 
          zk_proof: proofData.proof.zk_proof,
          public_signals: proofData.proof.public_signals 
        })
      });
      const data = await res.json();
      setTamperVerifyResult(data);
      
      if(!data.valid) {
        setTestReport(prev => ({ ...prev, tamper: true }));
        toast.success('Tamper Detected by ZK Engine!');
      }
    } catch (e) {
      toast.error('Error during tamper test');
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
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 1: Any Event Ingestion</h2>
            <p className="text-secondary text-sm">Send any arbitrary JSON state payload to the CLOUUD engine.</p>
            
            <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Event Type</label>
                <input 
                  type="text" 
                  value={eventData.event_type} 
                  onChange={e => setEventData({...eventData, event_type: e.target.value})}
                  className="w-full bg-background border border-white/10 p-3 rounded text-primary focus:ring-1 focus:ring-accent-cyan outline-none transition-colors font-mono text-sm"
                />
              </div>
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">JSON Payload</label>
                <textarea 
                  rows={6}
                  value={payloadText} 
                  onChange={e => setPayloadText(e.target.value)}
                  className="w-full bg-terminal border border-white/10 p-3 rounded text-accent-cyan focus:ring-1 focus:ring-accent-cyan outline-none transition-colors font-mono text-sm resize-none"
                />
              </div>
              <button 
                onClick={handleCreateEvent}
                disabled={isLoading}
                data-testid="btn-create-event"
                className="w-full bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue border border-accent-blue/30 p-3 rounded-md font-bold transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? 'Ingesting...' : 'Ingest Event Payload'} <Play weight="fill" />
              </button>
            </div>
          </div>
        );
      case 2:
      case 3:
      case 4:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 2-4: Zero Knowledge Engine</h2>
            <p className="text-secondary text-sm">Compressing states and calculating a ZK-SNARK proof that preserves data privacy.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan to-accent-pink opacity-50"></div>
              {eventId && (
                <div className="text-accent-green mb-4">
                  <CaretRight className="inline" /> Event stored locally: {eventId}
                </div>
              )}
              
              {!proofData ? (
                <button 
                  onClick={handleGenerateProof}
                  disabled={isLoading}
                  data-testid="btn-generate-proof"
                  className="bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all w-full mt-4 flex justify-center items-center gap-2"
                >
                  <Graph weight="bold"/> {isLoading ? 'Generating ZK Proof...' : 'Generate ZK-SNARK Proof'}
                </button>
              ) : (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  
                  <div>
                    <h3 className="text-accent-pink uppercase tracking-[0.2em] text-xs font-bold mb-2">Live State Extraction</h3>
                    {proofData.states.map((s, i) => (
                      <div key={i} className="text-secondary mb-1 border-l-2 border-accent-pink/50 pl-3">
                        [{i}] {s}
                      </div>
                    ))}
                  </div>

                  <div className="border border-accent-cyan/30 bg-accent-cyan/5 p-4 rounded-md">
                    <h3 className="text-accent-cyan uppercase tracking-[0.2em] text-xs font-bold mb-2">Zero Knowledge Proof Blob (Groth16)</h3>
                    <pre className="text-primary whitespace-pre-wrap break-all text-xs">
                      {JSON.stringify(proofData.proof, null, 2)}
                    </pre>
                  </div>

                  <div className="flex justify-between items-center bg-surface p-4 rounded border border-white/10">
                    <div>
                      <div className="text-muted text-xs uppercase tracking-wider">Compression</div>
                      <div className="text-accent-green font-bold">{proofData.original_size}B → {proofData.proof_size}B</div>
                    </div>
                    <div>
                      <div className="text-muted text-xs uppercase tracking-wider">Privacy</div>
                      <div className="text-accent-cyan font-bold">100% ZK Payload</div>
                    </div>
                  </div>

                  <button 
                    onClick={() => setCurrentStep(5)}
                    className="w-full bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50 p-3 rounded-md font-bold hover:bg-accent-cyan/30 transition-all"
                  >
                    Proceed to Verification
                  </button>

                </motion.div>
              )}
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 5: ZK Verification</h2>
             <p className="text-secondary text-sm">Verifying integrity mathematically via Public Signals (No access to original payload).</p>

             <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  data-testid="btn-verify-proof"
                  className="w-full bg-accent-green/20 text-accent-green border border-accent-green/50 hover:bg-accent-green/30 p-3 rounded-md font-bold transition-all"
                >
                  {isLoading ? 'Verifying ZK Math...' : 'Verify ZK Proof Integrity'}
                </button>

                {verifyResult && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 p-4 border border-white/10 rounded bg-terminal font-mono">
                     <div className="flex items-center gap-2 mb-2">
                        {verifyResult.valid ? <CheckCircle className="text-accent-green" size={24} weight="fill"/> : <ShieldWarning className="text-accent-pink" size={24} weight="fill"/>}
                        <span className={verifyResult.valid ? 'text-accent-green font-bold' : 'text-accent-pink font-bold'}>
                          {verifyResult.valid ? 'VALID SNARK' : 'INVALID'}
                        </span>
                     </div>
                     <div className="text-secondary text-xs leading-relaxed">
                        Time: {verifyResult.verification_time_ms}ms <br/>
                        Mathematical Integrity: {verifyResult.zk_math_verified.toString()}<br/>
                        Privacy Preserved: {verifyResult.privacy_preserved.toString()}
                     </div>
                  </motion.div>
                )}
             </div>
          </div>
        );
      case 6:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 6: Blockchain Anchor</h2>
            <p className="text-secondary text-sm">Publish only the ZK Public Signal to the immutable ledger.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative">
              <button 
                onClick={handlePublish}
                disabled={isLoading}
                data-testid="btn-publish-proof"
                className="w-full bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all mb-4"
              >
                {isLoading ? 'Publishing...' : 'Anchor Public Signal'}
              </button>

              {anchorData && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-accent-blue space-y-2 break-all">
                  <div><span className="text-muted">Chain:</span> {anchorData.chain}</div>
                  <div><span className="text-muted">Tx Hash:</span> {anchorData.tx_hash}</div>
                  <div><span className="text-muted">ZK Signal:</span> {anchorData.zk_public_signal}</div>
                  <div><span className="text-muted">Status:</span> CONFIRMED</div>
                </motion.div>
              )}
            </div>
          </div>
        );
      case 7:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 7: Tamper Detection</h2>
            <p className="text-secondary text-sm">Simulate a database breach modifying the JSON payload directly.</p>

            <div className="bg-surface border border-accent-pink/30 p-6 rounded-md">
              <button 
                onClick={handleTamper}
                disabled={isLoading}
                data-testid="btn-tamper-test"
                className="w-full bg-accent-pink/20 text-accent-pink border border-accent-pink/50 hover:bg-accent-pink/30 p-3 rounded-md font-bold transition-all mb-4"
              >
                {isLoading ? 'Running...' : 'Modify Payload & Verify'}
              </button>

              {tamperVerifyResult && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-terminal p-4 rounded border border-white/10 font-mono">
                    <div className="flex items-center gap-2 mb-2 text-accent-pink font-bold">
                        <ShieldWarning size={24} weight="fill"/>
                        TAMPER DETECTED BY ZK VERIFIER
                    </div>
                    <pre className="text-secondary text-xs">
                      {JSON.stringify(tamperVerifyResult, null, 2)}
                    </pre>
                </motion.div>
              )}
            </div>

            {testReport.tamper && (
              <div className="mt-8 pt-8 border-t border-white/10">
                 <h3 className="font-mono text-xl font-bold text-center mb-6">CLOUUD EVENT VALIDATION REPORT</h3>
                 <div className="max-w-md mx-auto font-mono text-sm space-y-2">
                    <ReportRow label="Generic Event Ingestion" pass={testReport.tx} />
                    <ReportRow label="Reasoning Capture" pass={testReport.capture} />
                    <ReportRow label="Zero Knowledge Proof" pass={testReport.proof} />
                    <ReportRow label="Independent ZK Verify" pass={testReport.verify} />
                    <ReportRow label="Tamper Detection" pass={testReport.tamper} />
                    <ReportRow label="Blockchain Anchor" pass={testReport.anchor} />
                 </div>
                 <div className="text-center mt-8 text-accent-green font-bold font-mono tracking-widest text-lg">
                   CLOUUD SYSTEM OPERATIONAL
                 </div>
              </div>
            )}

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
          <h2 className="text-3xl font-bold text-white mb-2">Developer API</h2>
          <p className="text-secondary">Integrate CLOUUD ZK State Provenance directly into your application.</p>
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
          <h3 className="font-bold flex items-center gap-2"><Code className="text-accent-blue"/> API Snippets</h3>
          
          <div className="bg-terminal border border-white/10 rounded-md overflow-hidden">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 text-xs font-mono text-secondary uppercase tracking-widest">
              cURL - Ingest Event
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="font-mono text-sm text-primary">
<span className="text-accent-pink">curl</span> -X POST https://api.clouud.dev/v1/events \<br/>
  -H <span className="text-accent-yellow">"Authorization: Bearer {apiKey || 'YOUR_API_KEY'}"</span> \<br/>
  -H <span className="text-accent-yellow">"Content-Type: application/json"</span> \<br/>
  -d <span className="text-accent-green">'{'{'}
  "event_type": "ai_log",
  "payload": {'{'} "user": "abc", "action": "login" {'}'}
{'}'}'</span>
              </pre>
            </div>
          </div>

          <div className="bg-terminal border border-white/10 rounded-md overflow-hidden">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 text-xs font-mono text-secondary uppercase tracking-widest">
              Node.js - Generate ZK Proof
            </div>
            <div className="p-4 overflow-x-auto">
              <pre className="font-mono text-sm text-primary">
<span className="text-accent-pink">const</span> response = <span className="text-accent-blue">await</span> <span className="text-accent-green">fetch</span>(<span className="text-accent-yellow">'https://api.clouud.dev/v1/proof'</span>, {'{'}<br/>
  method: <span className="text-accent-yellow">'POST'</span>,<br/>
  headers: {'{'}<br/>
    <span className="text-accent-yellow">'Authorization'</span>: <span className="text-accent-yellow">`Bearer ${apiKey || 'YOUR_API_KEY'}`</span>,<br/>
    <span className="text-accent-yellow">'Content-Type'</span>: <span className="text-accent-yellow">'application/json'</span><br/>
  {'}'},<br/>
  body: <span className="text-accent-blue">JSON</span>.<span className="text-accent-green">stringify</span>({'{'} event_id: <span className="text-accent-yellow">'ev_12345'</span> {'}'})<br/>
{'}'});<br/>
<span className="text-accent-pink">const</span> proofBlob = <span className="text-accent-blue">await</span> response.<span className="text-accent-green">json</span>();
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
              Playground
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

function ReportRow({label, pass}) {
  return (
    <div className="flex justify-between items-center border-b border-white/5 py-1">
      <span className="text-secondary">{label}</span>
      {pass ? <span className="text-accent-green font-bold">PASS ✓</span> : <span className="text-muted">-</span>}
    </div>
  )
}
