export interface TabItem { value: string; label: React.ReactNode; icon?: string; count?: number | string }
export interface TabsProps {
  items: Array<TabItem | string>;
  value?: string;
  onChange?: (value: string) => void;
  /** underline = page sections. pill = compact switcher inside a card or toolbar. */
  variant?: 'underline' | 'pill';
  className?: string;
}
export declare function Tabs(props: TabsProps): JSX.Element;
