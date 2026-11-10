export interface ProgressBarProps {
  /** 0–100. Ignored when indeterminate. */
  value?: number;
  tone?: 'accent' | 'success' | 'danger' | 'warning';
  /** 2px square-cornered variant — pinned under the top bar for page-level work. */
  thin?: boolean;
  indeterminate?: boolean;
  className?: string;
}
export declare function ProgressBar(props: ProgressBarProps): JSX.Element;
