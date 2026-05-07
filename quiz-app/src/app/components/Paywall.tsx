import { Lock, Zap, Check } from "lucide-react";
import SymbolSVG from "../../imports/Symbol.svg";
import { SEED_EVENTS, EventCard } from "./MainApp";

/**
 * Prototype paywall — sits between the onboarding "Done" screen and the
 * full app. Renders a peek of the user's Wednesday schedule behind a
 * bottom-sheet paywall card. ANY click anywhere on the screen advances
 * straight into the app.
 */
export default function Paywall({ onUnlock }: { onUnlock: () => void }) {
  const wednesday = SEED_EVENTS.filter((e) => e.day === 29 && e.inSchedule);

  return (
    <div className="paywall" onClick={onUnlock} role="dialog" aria-label="Unlock SideQuest">
      <div className="paywall__behind">
        <div className="paywall__day">
          <span className="paywall__day-dot" />
          Wednesday, April 29 · {wednesday.length} events
        </div>
        <h1 className="paywall__schedule-title">Your schedule</h1>
        <div className="paywall__events">
          {wednesday.map((e) => (
            <EventCard key={e.id} event={e} />
          ))}
        </div>
      </div>

      <div className="paywall__sheet">
        <div className="paywall__handle" />

        <div className="paywall__brand">
          <span className="paywall__lock"><Lock size={14} /></span>
          <img src={SymbolSVG} alt="" className="paywall__mark" />
        </div>

        <h2 className="paywall__heading">Unlock your full SideQuest</h2>
        <p className="paywall__sub">
          One-time payment. Full access to your TOKEN2049 plan, the AI agent, and every event.
        </p>

        <ul className="paywall__features">
          <li>
            <span className="paywall__feat-icon"><Zap size={14} /></span>
            Full personalized schedule across all days
          </li>
          <li>
            <span className="paywall__feat-icon"><Zap size={14} /></span>
            AI agent with chat, routing &amp; dress codes
          </li>
          <li>
            <span className="paywall__feat-icon paywall__feat-icon--check"><Check size={14} /></span>
            Add/remove events, see all 384 events
          </li>
        </ul>

        <div className="paywall__price">
          <span className="paywall__currency">$</span>
          <span className="paywall__amount">9.99</span>
        </div>
        <div className="paywall__price-sub">One-time · Lifetime access for this conference</div>

        <button className="paywall__cta" type="button">
          <svg width="16" height="20" viewBox="0 0 16 20" aria-hidden="true" className="paywall__cta-apple">
            <path
              fill="currentColor"
              d="M13.07 10.65c-.02-2.18 1.78-3.23 1.86-3.28-1.02-1.49-2.6-1.69-3.16-1.71-1.34-.13-2.62.79-3.3.79-.7 0-1.74-.77-2.86-.75-1.47.02-2.83.85-3.59 2.16-1.53 2.65-.39 6.57 1.1 8.72.73 1.05 1.6 2.23 2.74 2.19 1.1-.04 1.51-.71 2.84-.71 1.32 0 1.7.71 2.86.69 1.18-.02 1.93-1.07 2.65-2.13.84-1.22 1.18-2.4 1.2-2.46-.03-.01-2.3-.88-2.32-3.5zM10.92 4.04c.6-.74 1.01-1.75.9-2.77-.87.04-1.93.58-2.56 1.31-.56.65-1.05 1.69-.92 2.69.97.07 1.97-.49 2.58-1.23z"
            />
          </svg>
          <span>Buy with&nbsp;<span className="paywall__cta-pay">Pay</span></span>
        </button>
        <button className="paywall__alt" type="button">Other payment methods</button>

        <div className="paywall__footer">Secure checkout · Cancel anytime · Powered by Stripe</div>
      </div>
    </div>
  );
}
