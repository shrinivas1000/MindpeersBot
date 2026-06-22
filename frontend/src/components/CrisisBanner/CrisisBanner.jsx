/**
 * CrisisBanner — displayed inline when a crisis response is received.
 *
 * Styled distinctly with primary brand color accents (not alarming red).
 * Helpline numbers are rendered as tappable tel: links.
 */

import './CrisisBanner.css';

const HELPLINES = [
  {
    name: 'Tele MANAS',
    detail: 'Govt. of India, 24/7, multilingual',
    numbers: [
      { display: '14416', tel: '14416' },
      { display: '1-800-891-4416', tel: '18008914416' },
    ],
  },
  {
    name: 'KIRAN',
    detail: 'Govt. of India, 24/7',
    numbers: [
      { display: '1800-599-0019', tel: '18005990019' },
    ],
  },
  {
    name: 'Vandrevala Foundation',
    detail: '24/7',
    numbers: [
      { display: '1860-266-2345', tel: '18602662345' },
      { display: '1800-233-3330', tel: '18002333330' },
      { display: '+91 9999 666 555', tel: '+919999666555' },
    ],
  },
];

export default function CrisisBanner({ message }) {
  return (
    <div className="crisis-banner" id="crisis-banner" role="alert">
      <div className="crisis-banner__header">
        <svg className="crisis-banner__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
        </svg>
        <span className="crisis-banner__title">You are not alone</span>
      </div>

      <p className="crisis-banner__message">
        {message.content.split('\n').slice(0, 2).join(' ').substring(0, 200)}
      </p>

      <div className="crisis-banner__helplines">
        {HELPLINES.map((helpline) => (
          <div key={helpline.name} className="crisis-banner__helpline">
            <div className="crisis-banner__helpline-name">
              {helpline.name}
              <span className="crisis-banner__helpline-detail">{helpline.detail}</span>
            </div>
            <div className="crisis-banner__numbers">
              {helpline.numbers.map((num) => (
                <a
                  key={num.tel}
                  href={`tel:${num.tel}`}
                  className="crisis-banner__number"
                  id={`helpline-${num.tel}`}
                >
                  {num.display}
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="crisis-banner__footer">
        A trained person on the other end of these lines can help you right now. Please call.
      </p>
    </div>
  );
}
