import { useState } from 'react';
import { Sparkles, Clock, Scissors, Music, Wand2 } from 'lucide-react';
import { motion } from 'motion/react';

interface InstructionInputProps {
  instruction: string;
  onInstructionChange: (value: string) => void;
  disabled?: boolean;
}

const PRESET_INSTRUCTIONS = [
  {
    id: 'trim',
    label: '剪辑特定场景',
    icon: Scissors,
    prompt: '请帮我剪辑视频中最精彩的部分，保留高光时刻',
    category: 'basic',
  },
  {
    id: 'slow-motion',
    label: '添加慢动作',
    icon: Clock,
    prompt: '为关键镜头添加慢动作效果，使画面更具冲击力',
    category: 'effects',
  },
  {
    id: 'bgm',
    label: '添加背景音乐',
    icon: Music,
    prompt: '为视频添加合适的背景音乐，并调整音频混合',
    category: 'advanced',
  },
  {
    id: 'auto-edit',
    label: '智能编辑',
    icon: Wand2,
    prompt: '自动分析视频内容，智能剪辑并添加转场效果',
    category: 'advanced',
  },
];

export function InstructionInput({ instruction, onInstructionChange, disabled }: InstructionInputProps) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [showPresets, setShowPresets] = useState(true);

  const handlePresetClick = (preset: typeof PRESET_INSTRUCTIONS[0]) => {
    setSelectedPreset(preset.id);
    onInstructionChange(preset.prompt);
    setShowPresets(false);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onInstructionChange(e.target.value);
    setSelectedPreset(null);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="flex items-center gap-2 mb-3" style={{ color: 'var(--gray-900)' }}>
          <Sparkles className="text-[var(--primary-500)]" size={20} />
          <span>编辑指令</span>
        </label>

        <textarea
          value={instruction}
          onChange={handleTextChange}
          onFocus={() => setShowPresets(false)}
          disabled={disabled}
          placeholder="请输入您的视频编辑需求，例如：'剪辑前30秒的内容并添加淡入淡出效果'"
          className="w-full min-h-[120px] p-4 border border-[var(--gray-200)] rounded-lg resize-none
            focus:outline-none focus:border-[var(--primary-500)] focus:ring-2 focus:ring-[var(--primary-500)]/10
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--gray-50)]
            transition-all duration-200"
          style={{ 
            backgroundColor: 'white',
            color: 'var(--gray-900)',
          }}
        />

        {instruction && (
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 h-1 bg-[var(--gray-200)] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ 
                  width: instruction.length > 100 ? '100%' : instruction.length > 50 ? '66%' : '33%'
                }}
                className={`h-full transition-colors ${
                  instruction.length > 100 ? 'bg-[var(--success)]' : 
                  instruction.length > 50 ? 'bg-[var(--warning)]' : 
                  'bg-[var(--primary-500)]'
                }`}
              />
            </div>
            <span className="text-xs" style={{ color: 'var(--gray-400)' }}>
              {instruction.length > 100 ? '详细' : instruction.length > 50 ? '适中' : '简单'}
            </span>
          </div>
        )}
      </div>

      {showPresets && !instruction && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <div className="flex items-center gap-2">
            <div className="h-px flex-1 bg-[var(--gray-200)]" />
            <span className="text-xs" style={{ color: 'var(--gray-400)' }}>预设指令</span>
            <div className="h-px flex-1 bg-[var(--gray-200)]" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            {PRESET_INSTRUCTIONS.map((preset) => {
              const Icon = preset.icon;
              return (
                <motion.button
                  key={preset.id}
                  onClick={() => !disabled && handlePresetClick(preset)}
                  disabled={disabled}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-all duration-200
                    ${selectedPreset === preset.id 
                      ? 'border-[var(--primary-500)] bg-[var(--primary-50)]' 
                      : 'border-[var(--gray-200)] bg-white hover:border-[var(--primary-500)] hover:bg-[var(--gray-50)]'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className={`
                      w-10 h-10 rounded-lg flex items-center justify-center
                      ${selectedPreset === preset.id ? 'bg-[var(--primary-500)]' : 'bg-[var(--gray-100)]'}
                      transition-colors duration-200
                    `}>
                      <Icon 
                        className={selectedPreset === preset.id ? 'text-white' : 'text-[var(--gray-600)]'} 
                        size={20} 
                      />
                    </div>
                    <div className="flex-1">
                      <div className="text-sm mb-1" style={{ color: 'var(--gray-900)' }}>
                        {preset.label}
                      </div>
                      <div className="text-xs line-clamp-2" style={{ color: 'var(--gray-400)' }}>
                        {preset.prompt}
                      </div>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
}