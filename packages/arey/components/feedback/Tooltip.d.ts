export interface TooltipProps {
  /** Short, no period. Absolute timestamps and full values belong here. */
  label: React.ReactNode;
  /** Mono face — for SHAs and exact timestamps. */
  mono?: boolean;
  children: React.ReactNode;
  className?: string;
}
export declare function Tooltip(props: TooltipProps): JSX.Element;
