import type { EvaluateResponse } from "./api";

export type ReviewShellProps = {
  review: EvaluateResponse;
};

export function ReviewShell({ review }: ReviewShellProps) {
  return (
    <div className="review-section">
      <div className="review-metrics">
        <div className="metric-card">
          <span>Weighted score</span>
          <strong>{review.evaluation_result.weighted_score.toFixed(2)}</strong>
        </div>
        <div className="metric-card">
          <span>Confidence</span>
          <strong>{review.evaluation_result.overall_confidence.toFixed(2)}</strong>
        </div>
      </div>

      <div className="review-grid">
        <article className="review-card">
          <p className="panel-label">Strengths</p>
          <ul>
            {review.review_report.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="review-card">
          <p className="panel-label">Missed dimensions</p>
          <ul>
            {review.review_report.missed_dimensions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="review-card">
          <p className="panel-label">Reasoning gaps</p>
          <ul>
            {review.review_report.reasoning_gaps.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="review-card emphasis">
          <p className="panel-label">Next focus</p>
          <p>{review.review_report.recommended_next_focus}</p>
          {review.review_report.follow_up_handling_note ? (
            <p className="support-note">{review.review_report.follow_up_handling_note}</p>
          ) : null}
          {review.review_report.support_dependence_note ? (
            <p className="support-note">{review.review_report.support_dependence_note}</p>
          ) : null}
        </article>
      </div>
    </div>
  );
}
