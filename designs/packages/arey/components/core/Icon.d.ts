export interface IconProps {
  /** Phosphor icon name without prefix, e.g. "house", "gear-six", "arrow-up-right". */
  name: string;
  /** Pixel size. 14 inline, 16 controls, 20 mobile tab bar, 24 empty states. */
  size?: number;
  /** Phosphor weight. "fill" indicates a selected state only. */
  weight?: 'thin' | 'light' | 'regular' | 'bold' | 'fill' | 'duotone';
  /** Overrides currentColor. Avoid unless the adjacent label is also accented. */
  color?: string;
  /** Accessible label. Omit for purely decorative icons (renders aria-hidden). */
  label?: string;
  className?: string;
  style?: React.CSSProperties;
}
export declare function Icon(props: IconProps): JSX.Element;
