import { useMemo } from "react";
import "./AppSection.scss";

type SectionProps = {
  name: string;
  tasks: {
    name: string;
    updated_at: string;
  }[];
};

export const AppSection = (props: SectionProps) => {
  const { name, tasks } = props;
  const parsedTasks = useMemo(
    () =>
      tasks.map((t) => ({
        ...t,
        updated_at: new Date(t.updated_at).toLocaleString("ja-JP"),
      })),
    [tasks],
  );

  return (
    <section className="section">
      <h2 className="name">{name}</h2>
      <table className="task-table">
        <thead className="header">
          <tr>
            <th>name</th>
            <th>updated</th>
          </tr>
        </thead>
        <tbody className="body">
          {parsedTasks.length ? (
            parsedTasks.map((t, idx) => (
              <tr key={idx}>
                <td>{t.name}</td>
                <td>{t.updated_at}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={2} className="placeholder">
                no tasks
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
};
