import { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, XCircle, Clock } from 'lucide-react';
import { motion } from 'motion/react';

interface ProcessStep {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
  steps: ProcessStep[];
  progress: number;
  estimatedTime?: number;
  currentIteration?: number;
  totalIterations?: number;
}

export function ProgressIndicator({
  currentStep,
  totalSteps,
  steps,
  progress,
  estimatedTime,
  currentIteration = 1,
  totalIterations = 1,
}: ProgressIndicatorProps) {
  const [displayProgress, setDisplayProgress] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDisplayProgress(progress);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  };

  return (
    <div className="space-y-6">
      {/* 总体进度条 */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-base" style={{ color: 'var(--gray-900)' }}>
              处理进度
            </h3>
            <div className="px-3 py-1 rounded-full text-xs" style={{ 
              backgroundColor: 'var(--primary-100)', 
              color: 'var(--primary-600)' 
            }}>
              第 {currentIteration} 轮 / 共 {totalIterations} 轮
            </div>
          </div>
          <span className="text-2xl" style={{ color: 'var(--primary-600)' }}>
            {Math.round(displayProgress)}%
          </span>
        </div>

        <div className="relative h-3 bg-[var(--gray-200)] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${displayProgress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-[var(--primary-500)] to-[var(--primary-600)] relative"
          >
            <motion.div
              className="absolute inset-0 bg-white/30"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>
        </div>

        {estimatedTime !== undefined && estimatedTime > 0 && (
          <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--gray-600)' }}>
            <Clock size={16} />
            <span>预计剩余时间: {formatTime(estimatedTime)}</span>
          </div>
        )}
      </div>

      {/* 详细步骤 */}
      <div className="space-y-4">
        <h4 className="text-sm" style={{ color: 'var(--gray-600)' }}>
          处理步骤
        </h4>
        
        <div className="space-y-3">
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = step.status === 'completed';
            const isError = step.status === 'error';
            const isPending = step.status === 'pending';

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`
                  flex items-start gap-4 p-4 rounded-lg border-2 transition-all duration-200
                  ${isActive ? 'border-[var(--primary-500)] bg-[var(--primary-50)]' : 
                    isCompleted ? 'border-[var(--success)]/30 bg-[var(--success)]/5' :
                    isError ? 'border-[var(--error)]/30 bg-[var(--error)]/5' :
                    'border-[var(--gray-200)] bg-white'
                  }
                `}
              >
                <div className={`
                  w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                  ${isActive ? 'bg-[var(--primary-500)]' :
                    isCompleted ? 'bg-[var(--success)]' :
                    isError ? 'bg-[var(--error)]' :
                    'bg-[var(--gray-200)]'
                  }
                `}>
                  {isActive && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <Loader2 className="text-white" size={20} />
                    </motion.div>
                  )}
                  {isCompleted && <CheckCircle2 className="text-white" size={20} />}
                  {isError && <XCircle className="text-white" size={20} />}
                  {isPending && <span className="text-sm text-[var(--gray-600)]">{index + 1}</span>}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h5 className="text-sm" style={{ 
                      color: isActive ? 'var(--primary-600)' : 
                             isCompleted ? 'var(--success)' : 
                             isError ? 'var(--error)' : 
                             'var(--gray-600)' 
                    }}>
                      {step.label}
                    </h5>
                    {isActive && (
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="w-2 h-2 rounded-full bg-[var(--primary-500)]"
                      />
                    )}
                  </div>
                  <p className="text-xs" style={{ color: 'var(--gray-400)' }}>
                    {step.description}
                  </p>
                </div>

                {isCompleted && (
                  <div className="text-xs px-2 py-1 rounded" style={{ 
                    backgroundColor: 'var(--success)', 
                    color: 'white' 
                  }}>
                    已完成
                  </div>
                )}
                {isError && (
                  <div className="text-xs px-2 py-1 rounded" style={{ 
                    backgroundColor: 'var(--error)', 
                    color: 'white' 
                  }}>
                    失败
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
