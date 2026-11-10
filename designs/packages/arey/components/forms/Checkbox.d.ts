export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  /** Secondary line under the label. */
  description?: React.ReactNode;
  /** Mixed state — used by table select-all headers. */
  indeterminate?: boolean;
}
export declare function Checkbox(props: CheckboxProps): JSX.Element;
