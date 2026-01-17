'use client';

interface RunButtonProps {
  onClick: () => void;
  isRunning: boolean;
  variant?: 'run' | 'submit';
}

export function RunButton({ onClick, isRunning, variant = 'run' }: RunButtonProps) {
  const styles = {
    run: 'bg-green-600 hover:bg-green-700',
    submit: 'bg-primary-600 hover:bg-primary-700',
  };

  const labels = {
    run: isRunning ? 'Running...' : 'Run',
    submit: isRunning ? 'Submitting...' : 'Submit',
  };

  return (
    <button
      onClick={onClick}
      disabled={isRunning}
      className={`px-4 py-2 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${styles[variant]}`}
    >
      {labels[variant]}
    </button>
  );
}
