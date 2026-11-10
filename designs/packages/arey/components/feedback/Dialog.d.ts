export interface DialogProps {
  open?: boolean;
  title?: React.ReactNode;
  description?: React.ReactNode;
  /** Action row, right-aligned on a subtle fill. Cancel first, primary last. */
  footer?: React.ReactNode;
  /** md = 440px, lg = 640px, sheet = bottom sheet (mobile). */
  size?: 'md' | 'lg' | 'sheet';
  /** Enables Escape, scrim click, and the close button. */
  onClose?: () => void;
  className?: string;
  children?: React.ReactNode;
}
export declare function Dialog(props: DialogProps): JSX.Element | null;
