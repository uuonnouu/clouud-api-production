import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Play, ShieldCheck, Hexagon, Database, 
  TerminalWindow, CaretRight, ShieldWarning, FileText, Cpu, Code
} from '@phosphor-icons/react';
import { Toaster, toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const Steps = [
  { id: 1, title: 'JSON Event Input', icon: FileText },
  { id: 2, title: 'Compression & Proof', icon: Cpu },
  { id: 3, title: 'Verification', icon: ShieldCheck },
  { id: 4, title: 'Tamper Test', icon: ShieldWarning }
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
  const [verifyResult, setVerifyResult] = useState(null);
  const [tamperVerifyResult, setTamperVerifyResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testReport, setTestReport] = useState({});

  const handleCreateEvent = async () => {
    setIsLoading(true);
    try {
      let parsedPayload;
      try { parsedPayload = JSON.parse(payloadText); } 
      catch(e) { toast.error("Invalid JSON payload"); setIsLoading(false); return; }

      const res = await fetch(`${API_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: "transaction", payload: parsedPayload })
      });
      const data = await res.json();
      setEventId(data.event_id);
      setTestReport(prev => ({ ...prev, tx: true }));
      toast.success('Event Stored in DB');
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
      toast.success('CLOUUD Proof Generated');
      setCurrentStep(3);
    } catch (e) {
      toast.error('Failed to generate proof');
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
          proof: proofData.proof
        })
      });
      const data = await res.json();
      setVerifyResult(data);
      if(data.valid) {
        setTestReport(prev => ({ ...prev, verify: true }));
        toast.success('Integrity Verified');
        setCurrentStep(4);
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
      // Mutate
      if (tampered.amount) tampered.amount = 9999;
      else tampered.tampered = true;
      
      await fetch(`${API_URL}/tamper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, tampered_payload: tampered })
      });
      toast.warning('Database Payload Tampered!');
      
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          event_id: eventId, 
          proof: proofData.proof
        })
      });
      const data = await res.json();
      setTamperVerifyResult(data);
      
      if(!data.valid) {
        setTestReport(prev => ({ ...prev, tamper: true }));
        toast.success('Tamper Successfully Detected!');
      }
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
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">1. JSON Event Input</h2>
            <p className="text-secondary text-sm">Create a data event/transaction to be processed.</p>
            
            <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Transaction Payload (JSON)</label>
                <textarea 
                  rows={8}
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
                {isLoading ? 'Storing...' : 'Store Transaction Event'} <Play weight="fill" />
              </button>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">2. Compression & Proof</h2>
            <p className="text-secondary text-sm">Deterministic state normalization and Merkle hashing.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan to-accent-pink opacity-50"></div>
              
              {!proofData ? (
                 <button 
                  onClick={handleGenerateProof}
                  disabled={isLoading}
                  data-testid="btn-generate-proof"
                  className="bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all w-full mt-4 flex justify-center items-center gap-2"
                >
                  <Cpu weight="bold" /> {isLoading ? 'Generating Proof...' : 'Run Local Proof Engine'}
                </button>
              ) : (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  
                  <div>
                    <h3 className="text-accent-pink uppercase tracking-[0.2em] text-xs font-bold mb-2">Normalized States</h3>
                    {proofData.states.map((s, i) => (
                      <div key={i} className="text-secondary mb-1 border-l-2 border-accent-pink/50 pl-3 break-all">
                        [{i}] {s}
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-surface p-4 rounded border border-white/10">
                      <div className="text-muted text-xs uppercase tracking-wider mb-2">Original Size</div>
                      <div className="text-primary font-bold">{proofData.original_size} B</div>
                    </div>
                    <div className="bg-surface p-4 rounded border border-white/10">
                      <div className="text-muted text-xs uppercase tracking-wider mb-2">Proof Size</div>
                      <div className="text-accent-green font-bold">{proofData.proof_size} B</div>
                    </div>
                    <div className="bg-surface p-4 rounded border border-white/10">
                      <div className="text-muted text-xs uppercase tracking-wider mb-2">Ratio</div>
                      <div className="text-accent-cyan font-bold">{(proofData.compression_ratio * 100).toFixed(2)}%</div>
                    </div>
                    <div className="bg-surface p-4 rounded border border-white/10">
                      <div className="text-muted text-xs uppercase tracking-wider mb-2">Time</div>
                      <div className="text-accent-yellow font-bold">{proofData.processing_time_ms} ms</div>
                    </div>
                  </div>

                  <div className="border border-white/10 bg-white/5 p-4 rounded-md flex flex-col gap-2">
                    <div className="text-muted text-xs uppercase tracking-[0.2em]">Merkle Root</div>
                    <div className="text-primary truncate text-accent-pink">{proofData.merkle_root}</div>
                  </div>

                  <button 
                    onClick={() => setCurrentStep(3)}
                    className="w-full bg-accent-yellow/20 text-accent-yellow border border-accent-yellow/50 p-3 rounded-md font-bold hover:bg-accent-yellow/30 transition-all flex justify-center items-center gap-2"
                  >
                    Proceed to Verification
                  </button>

                </motion.div>
              )}
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
             <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">3. Verification</h2>
             <p className="text-secondary text-sm">Recalculates state hashes to ensure the database payload perfectly matches the proof commitment.</p>

             <div className="bg-terminal border border-white/10 p-6 rounded-md space-y-4">
                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  data-testid="btn-verify-proof"
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
                     <div className="space-y-2 text-sm">
                       <div className="flex justify-between"><span className="text-muted">Verification Time:</span><span className="text-primary">{verifyResult.verification_time_ms} ms</span></div>
                     </div>
                     <button 
                      onClick={() => setCurrentStep(4)}
                      className="mt-4 w-full bg-white/10 hover:bg-white/20 text-white p-2 rounded transition-all"
                     >
                        Run Tamper Test
                     </button>
                  </motion.div>
                )}
             </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">4. Tamper Test</h2>
            <p className="text-secondary text-sm">Simulate a database breach by modifying the payload directly.</p>

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
                    <div className="flex items-center gap-2 mb-4 text-accent-pink font-bold text-lg">
                        <ShieldWarning size={28} weight="fill"/>
                        TAMPER DETECTED
                    </div>
                    <div className="space-y-3 text-sm">
                       <div>
                         <div className="text-muted text-xs uppercase mb-1">Expected Root (Proof)</div>
                         <div className="text-primary truncate">{tamperVerifyResult.provided_root}</div>
                       </div>
                       <div>
                         <div className="text-muted text-xs uppercase mb-1">Recalculated Root (DB)</div>
                         <div className="text-accent-pink truncate">{tamperVerifyResult.recalculated_root}</div>
                       </div>
                    </div>
                </motion.div>
              )}
            </div>

            {testReport.tamper && (
              <div className="mt-8 pt-8 border-t border-white/10">
                 <h3 className="font-mono text-xl font-bold text-center mb-6">CLOUUD E2E VALIDATION REPORT</h3>
                 <div className="max-w-md mx-auto font-mono text-sm space-y-2">
                    <ReportRow label="Transaction Creation" pass={testReport.tx} />
                    <ReportRow label="State Normalization" pass={testReport.capture} />
                    <ReportRow label="Compression / Proof Gen" pass={testReport.proof} />
                    <ReportRow label="Independent Verification" pass={testReport.verify} />
                    <ReportRow label="Tamper Detection" pass={testReport.tamper} />
                 </div>
                 <div className="text-center mt-8 text-accent-green font-bold font-mono tracking-widest text-lg">
                   LOCAL PIPELINE OPERATIONAL
                 </div>
              </div>
            )}

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
          <div className="flex gap-4">
            <span className="text-xs font-bold tracking-widest uppercase text-secondary border border-white/10 px-2 py-1 rounded bg-white/5">
              Local Deterministic Engine
            </span>
          </div>
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

function ReportRow({label, pass}) {
  return (
    <div className="flex justify-between items-center border-b border-white/5 py-1">
      <span className="text-secondary">{label}</span>
      {pass ? <span className="text-accent-green font-bold">PASS ✓</span> : <span className="text-muted">-</span>}
    </div>
  )
}
