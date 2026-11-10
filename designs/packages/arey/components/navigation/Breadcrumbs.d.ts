export interface BreadcrumbsProps {
  items: Array<{ label: React.ReactNode; href?: string }>;
  className?: string;
}
export declare function Breadcrumbs(props: BreadcrumbsProps): JSX.Element;
