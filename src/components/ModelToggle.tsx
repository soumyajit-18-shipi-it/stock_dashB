import { Brain, TreeDeciduous } from 'lucide-react';
import { useStore } from '../store/stock_store';

export function ModelToggle() {
  const { model, setModel } = useStore();

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-400 mr-2">Model:</span>
      <div className="flex bg-slate-800 rounded-lg p-1">
        <button
          onClick={() => setModel('linear')}
          className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            model === 'linear'
              ? 'bg-emerald-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-700'
          }`}
        >
          <Brain className="h-4 w-4" />
          Linear
        </button>
        <button
          onClick={() => setModel('rf')}
          className={`flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            model === 'rf'
              ? 'bg-emerald-600 text-white'
              : 'text-slate-400 hover:text-white hover:bg-slate-700'
          }`}
        >
          <TreeDeciduous className="h-4 w-4" />
          Random Forest
        </button>
      </div>
    </div>
  );
}
