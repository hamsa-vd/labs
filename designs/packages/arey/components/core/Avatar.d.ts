export interface AvatarProps {
  /** Used for initials fallback and the title attribute. */
  name?: string;
  src?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Square with 8px radius — used for projects and orgs, not people. */
  square?: boolean;
  tone?: 'neutral' | 'accent';
  className?: string;
}
export declare function Avatar(props: AvatarProps): JSX.Element;
export interface AvatarStackProps {
  people: Array<{ name?: string; src?: string }>;
  /** Overflow collapses into a "+n" chip. */
  max?: number;
  size?: 'xs' | 'sm' | 'md';
}
export declare function AvatarStack(props: AvatarStackProps): JSX.Element;
