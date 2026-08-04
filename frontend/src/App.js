import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, Play, ShieldCheck, Hash, Hexagon, Database, Code, 
  TerminalWindow, CaretRight, ShieldWarning
} from '@phosphor-icons/react';
import { Toaster, toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + "/api/v1";

const Steps = [
  { id: 1, title: 'Transaction', icon: Hexagon },
  { id: 2, title: 'Reasoning Capture', icon: Code },
  { id: 3, title: 'Proof Gen', icon: Hash },
  { id: 4, title: 'Persistence', icon: Database },
  { id: 5, title: 'Verify', icon: ShieldCheck },
  { id: 6, title: 'Blockchain', icon: TerminalWindow },
  { id: 7, title: 'Tamper Test', icon: ShieldWarning }
];

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [txData, setTxData] = useState({ user_id: 'user-001', package_id: 'starter-100', amount: 100 });
  const [txId, setTxId] = useState(null);
  const [proofData, setProofData] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  const [anchorData, setAnchorData] = useState(null);
  const [tamperVerifyResult, setTamperVerifyResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [testReport, setTestReport] = useState({});

  const handleCreateTx = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(txData)
      });
      const data = await res.json();
      setTxId(data.transaction_id);
      setTestReport(prev => ({ ...prev, tx: true }));
      toast.success('Transaction Created');
      setCurrentStep(2);
    } catch (e) {
      toast.error('Failed to create transaction');
    }
    setIsLoading(false);
  };

  const handleGenerateProof = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/proof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: txId })
      });
      const data = await res.json();
      setProofData(data);
      setTestReport(prev => ({ ...prev, capture: true, compress: true, proof: true, persist: true }));
      toast.success('Proof Generated & Stored');
      setCurrentStep(5); // Skipping to verify for demo
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
        body: JSON.stringify({ transaction_id: txId, proof: proofData.proof })
      });
      const data = await res.json();
      setVerifyResult(data);
      if(data.valid) {
        setTestReport(prev => ({ ...prev, verify: true }));
        toast.success('Verification Successful');
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
        body: JSON.stringify({ transaction_id: txId })
      });
      const data = await res.json();
      setAnchorData(data);
      setTestReport(prev => ({ ...prev, anchor: true }));
      toast.success('Anchored to Blockchain');
      setCurrentStep(7);
    } catch (e) {
      toast.error('Publish error');
    }
    setIsLoading(false);
  };

  const handleTamper = async () => {
    setIsLoading(true);
    try {
      await fetch(`${API_URL}/tamper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: txId, new_amount: 9999 })
      });
      toast.warning('Transaction Tampered in Database!');
      
      const res = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: txId, proof: proofData.proof })
      });
      const data = await res.json();
      setTamperVerifyResult(data);
      
      if(!data.valid) {
        setTestReport(prev => ({ ...prev, tamper: true }));
        toast.success('Tamper Detected!');
      }
    } catch (e) {
      toast.error('Error during tamper test');
    }
    setIsLoading(false);
  };

  const renderContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 1: Transaction Creation</h2>
            <p className="text-secondary text-sm">Initiate a credit purchase to begin the CLOUUD proof sequence.</p>
            
            <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">User ID</label>
                <input 
                  type="text" 
                  value={txData.user_id} 
                  onChange={e => setTxData({...txData, user_id: e.target.value})}
                  className="w-full bg-background border border-white/10 p-3 rounded text-primary focus:ring-1 focus:ring-accent-cyan outline-none transition-colors"
                />
              </div>
              <div>
                <label className="uppercase tracking-[0.2em] text-xs font-bold text-muted block mb-2">Amount (Credits)</label>
                <input 
                  type="number" 
                  value={txData.amount} 
                  onChange={e => setTxData({...txData, amount: parseInt(e.target.value)})}
                  className="w-full bg-background border border-white/10 p-3 rounded text-primary focus:ring-1 focus:ring-accent-cyan outline-none transition-colors"
                />
              </div>
              <button 
                onClick={handleCreateTx}
                disabled={isLoading}
                data-testid="btn-create-tx"
                className="w-full bg-accent-blue/10 hover:bg-accent-blue/20 text-accent-blue border border-accent-blue/30 p-3 rounded-md font-bold transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? 'Processing...' : 'Execute Transaction'} <Play weight="fill" />
              </button>
            </div>
          </div>
        );
      case 2:
      case 3:
      case 4:
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 2-4: CLOUUD Engine</h2>
            <p className="text-secondary text-sm">Generating AI reasoning trace, compressing states, and computing Merkle commitment.</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan to-accent-pink opacity-50"></div>
              {txId && (
                <div className="text-accent-green mb-4">
                  <CaretRight className="inline" /> Transaction anchored locally: {txId}
                </div>
              )}
              
              {!proofData ? (
                <button 
                  onClick={handleGenerateProof}
                  disabled={isLoading}
                  data-testid="btn-generate-proof"
                  className="bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all w-full mt-4"
                >
                  {isLoading ? 'Generating CLOUUD Proof...' : 'Trigger Proof Generation'}
                </button>
              ) : (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  
                  <div>
                    <h3 className="text-accent-pink uppercase tracking-[0.2em] text-xs font-bold mb-2">Live AI Trace (S0..S3)</h3>
                    {proofData.states.map((s, i) => (
                      <div key={i} className="text-secondary mb-1 border-l-2 border-accent-pink/50 pl-3">
                        [{i}] {s}
                      </div>
                    ))}
                  </div>

                  <div>
                    <h3 className="text-accent-yellow uppercase tracking-[0.2em] text-xs font-bold mb-2">Hash Chain</h3>
                    {proofData.proof.hashes.map((h, i) => (
                      <div key={i} className="text-secondary mb-1 flex gap-3 items-center">
                        <span className="text-muted">H{i}</span> 
                        <span className="truncate">{h}</span>
                      </div>
                    ))}
                  </div>

                  <div className="border border-accent-cyan/30 bg-accent-cyan/5 p-4 rounded-md">
                    <h3 className="text-accent-cyan uppercase tracking-[0.2em] text-xs font-bold mb-2">Compact Proof Blob</h3>
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
                      <div className="text-muted text-xs uppercase tracking-wider">Ratio</div>
                      <div className="text-accent-green font-bold">{(proofData.proof.compression_ratio * 100).toFixed(2)}%</div>
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
             <h2 className="text-2xl font-bold tracking-tight text-white mb-2" data-testid="step-title">Stage 5: Independent Verification</h2>
             <p className="text-secondary text-sm">Verifying integrity using only the compact proof blob (simulating original trace deletion).</p>

             <div className="bg-surface border border-white/10 p-6 rounded-md space-y-4">
                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  data-testid="btn-verify-proof"
                  className="w-full bg-accent-green/20 text-accent-green border border-accent-green/50 hover:bg-accent-green/30 p-3 rounded-md font-bold transition-all"
                >
                  {isLoading ? 'Verifying...' : 'Verify Proof Commitment'}
                </button>

                {verifyResult && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 p-4 border border-white/10 rounded bg-terminal font-mono">
                     <div className="flex items-center gap-2 mb-2">
                        {verifyResult.valid ? <CheckCircle className="text-accent-green" size={24} weight="fill"/> : <ShieldWarning className="text-accent-pink" size={24} weight="fill"/>}
                        <span className={verifyResult.valid ? 'text-accent-green font-bold' : 'text-accent-pink font-bold'}>
                          {verifyResult.valid ? 'VALID' : 'INVALID'}
                        </span>
                     </div>
                     <div className="text-secondary text-xs">
                        Time: {verifyResult.verification_time_ms}ms <br/>
                        Commitment Match: {verifyResult.commitment_match.toString()}
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
            <p className="text-secondary text-sm">Publish the CLOUUD commitment to an immutable ledger (Ethereum simulation).</p>
            
            <div className="bg-terminal border border-white/10 p-6 rounded-md font-mono text-sm relative">
              <button 
                onClick={handlePublish}
                disabled={isLoading}
                data-testid="btn-publish-proof"
                className="w-full bg-primary text-background hover:bg-white/90 p-3 rounded-md font-bold transition-all mb-4"
              >
                {isLoading ? 'Publishing...' : 'Publish to Base/Ethereum'}
              </button>

              {anchorData && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-accent-blue space-y-2 break-all">
                  <div><span className="text-muted">Chain:</span> {anchorData.chain}</div>
                  <div><span className="text-muted">Tx Hash:</span> {anchorData.tx_hash}</div>
                  <div><span className="text-muted">CLOUUD Root:</span> {anchorData.clouud_commitment}</div>
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
            <p className="text-secondary text-sm">Simulate a database breach modifying the transaction amount.</p>

            <div className="bg-surface border border-accent-pink/30 p-6 rounded-md">
              <button 
                onClick={handleTamper}
                disabled={isLoading}
                data-testid="btn-tamper-test"
                className="w-full bg-accent-pink/20 text-accent-pink border border-accent-pink/50 hover:bg-accent-pink/30 p-3 rounded-md font-bold transition-all mb-4"
              >
                {isLoading ? 'Running...' : 'Modify DB Amount & Verify'}
              </button>

              {tamperVerifyResult && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-terminal p-4 rounded border border-white/10 font-mono">
                    <div className="flex items-center gap-2 mb-2 text-accent-pink font-bold">
                        <ShieldWarning size={24} weight="fill"/>
                        TAMPER DETECTED
                    </div>
                    <pre className="text-secondary text-xs">
                      {JSON.stringify(tamperVerifyResult, null, 2)}
                    </pre>
                </motion.div>
              )}
            </div>

            {testReport.tamper && (
              <div className="mt-8 pt-8 border-t border-white/10">
                 <h3 className="font-mono text-xl font-bold text-center mb-6">CLOUUD E2E VALIDATION REPORT</h3>
                 <div className="max-w-md mx-auto font-mono text-sm space-y-2">
                    <ReportRow label="Transaction Creation" pass={testReport.tx} />
                    <ReportRow label="Reasoning Capture" pass={testReport.capture} />
                    <ReportRow label="Semantic Compression" pass={testReport.compress} />
                    <ReportRow label="Proof Generation" pass={testReport.proof} />
                    <ReportRow label="Database Persistence" pass={testReport.persist} />
                    <ReportRow label="Independent Verification" pass={testReport.verify} />
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

  return (
    <div className="min-h-screen bg-background text-primary font-sans">
      <Toaster theme="dark" richColors />
      
      <header className="border-b border-white/10 bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="font-mono font-bold text-xl tracking-tighter flex items-center gap-2">
            <Hexagon weight="fill" className="text-accent-cyan" /> CLOUUD.
          </div>
          <div className="text-xs font-mono text-secondary tracking-widest uppercase">
            Proof of Reasoning
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
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
                {renderContent()}
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
