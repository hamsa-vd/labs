export interface FieldProps {
  label?: React.ReactNode;
  /** Helper text. No trailing period on single clauses. */
  hint?: React.ReactNode;
  /** Replaces the hint when present and colours it danger. */
  error?: React.ReactNode;
  /** Renders an "Optional" marker beside the label — arey never marks required. */
  optional?: boolean;
  htmlFor?: string;
  /** row = 200px label column, used in Settings. */
  layout?: 'stack' | 'row';
  className?: string;
  children?: React.ReactNode;
}
export declare function Field(props: FieldProps): JSX.Element;
