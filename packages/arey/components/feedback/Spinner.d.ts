export interface SpinnerProps {
  size?: number;
  /** Border width. Defaults to size/9, min 1.5px. */
  thickness?: number;
  className?: string;
  style?: React.CSSProperties;
}
export declare function Spinner(props: SpinnerProps): JSX.Element;
