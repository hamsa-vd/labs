import type React from 'react';

export interface TableProps extends React.TableHTMLAttributes<HTMLTableElement> {}
export interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {
  align?: 'left' | 'center' | 'right';
}
export interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  align?: 'left' | 'center' | 'right';
  mono?: boolean;
}
export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  interactive?: boolean;
}

export declare function Table(props: TableProps): React.JSX.Element;
export declare function TableHead(props: TableHeadProps): React.JSX.Element;
export declare function TableCell(props: TableCellProps): React.JSX.Element;
export declare function TableRow(props: TableRowProps): React.JSX.Element;
