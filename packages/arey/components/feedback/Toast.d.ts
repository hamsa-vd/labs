export interface ToastProps {
  tone?: 'neutral' | 'success' | 'danger' | 'warning';
  /** One clause, sentence case, no exclamation mark. */
  title: React.ReactNode;
  description?: React.ReactNode;
  /** Optional single action — usually a link-variant Button ("View logs"). */
  action?: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
}
export declare function Toast(props: ToastProps): JSX.Element;
export interface ToastRegionProps { children?: React.ReactNode }
export declare function ToastRegion(props: ToastRegionProps): JSX.Element;
