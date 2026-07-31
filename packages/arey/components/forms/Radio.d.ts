export interface RadioProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  description?: React.ReactNode;
}
export declare function Radio(props: RadioProps): JSX.Element;
export interface RadioGroupProps {
  name: string;
  value?: string;
  onChange?: (value: string) => void;
  options: Array<{ value: string; label: React.ReactNode; description?: React.ReactNode }>;
  direction?: 'column' | 'row';
  className?: string;
}
export declare function RadioGroup(props: RadioGroupProps): JSX.Element;
