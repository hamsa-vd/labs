export interface SegmentedControlProps {
  options: Array<{ value: string; label?: React.ReactNode; icon?: string } | string>;
  value?: string;
  onChange?: (value: string) => void;
  size?: 'md' | 'lg';
  /** Shrink to content instead of filling the container. */
  inline?: boolean;
  className?: string;
}
export declare function SegmentedControl(props: SegmentedControlProps): JSX.Element;
