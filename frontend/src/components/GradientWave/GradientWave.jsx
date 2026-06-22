/**
 * GradientWave — reusable ambient gradient element.
 *
 * Full-size on landing hero (decorative backdrop orb),
 * thin gradient strip under the chat header.
 * The `compact` prop controls which mode.
 */

import './GradientWave.css';

export default function GradientWave({ compact = false }) {
  if (compact) {
    return (
      <div className="gradient-wave gradient-wave--compact">
        <div className="gradient-wave__strip" aria-hidden="true" />
      </div>
    );
  }

  return (
    <div className="gradient-wave gradient-wave--full" aria-hidden="true">
      <div className="gradient-wave__orb gradient-wave__orb--1" />
      <div className="gradient-wave__orb gradient-wave__orb--2" />
      <div className="gradient-wave__orb gradient-wave__orb--3" />
    </div>
  );
}
