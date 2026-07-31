export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Mono face — env vars, config, log paste. */
  mono?: boolean;
  invalid?: boolean;
  rows?: number;
}
export declare function Textarea(props: TextareaProps): JSX.Element;
