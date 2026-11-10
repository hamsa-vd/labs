export interface KbdProps {
  /** "cmd+k" or ['cmd','shift','p']. Modifier names map to unicode glyphs. */
  keys: string | string[];
  className?: string;
}
export declare function Kbd(props: KbdProps): JSX.Element;
