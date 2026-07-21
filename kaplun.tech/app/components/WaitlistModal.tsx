"use client";

import { useState } from "react";
import { useWaitlist } from "@clerk/nextjs";

export function WaitlistModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { waitlist, errors, fetchStatus } = useWaitlist();
  const [email, setEmail] = useState("");
  const [duplicateEmail, setDuplicateEmail] = useState(false);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const { error } = await waitlist.join({ emailAddress: email });
    if (error) {
      const isDuplicate =
        (error as any)?.errors?.[0]?.code === "form_identifier_exists";
      if (isDuplicate) {
        setDuplicateEmail(true);
      } else {
        console.error("Failed to join waitlist:", error);
      }
    }
  };

  // Already on the waitlist (new signup or already registered)
  if (waitlist.id || duplicateEmail) {
    const isAlreadyRegistered = duplicateEmail && !waitlist.id;
    return (
      // eslint-disable-next-line jsx-a11y/no-static-element-interactions
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 50,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(10, 10, 10, 0.5)",
          backdropFilter: "blur(8px)",
        }}
        onClick={onClose}
        onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
      >
        {/* eslint-disable-next-line jsx-a11y/no-static-element-interactions */}
        <div
          style={{
            background: "var(--clay-surface-card)",
            borderRadius: "var(--clay-rounded-xl)",
            padding: "var(--clay-spacing-2xl)",
            maxWidth: 440,
            width: "90%",
            textAlign: "center",
          }}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <div style={{ fontSize: 48, marginBottom: "var(--clay-spacing-md)" }}>
            {isAlreadyRegistered ? "👋" : "🎉"}
          </div>
          <h2
            style={{
              fontSize: "var(--clay-title-lg)",
              fontWeight: 600,
              color: "var(--clay-ink)",
              marginBottom: "var(--clay-spacing-xs)",
            }}
          >
            {isAlreadyRegistered ? "Already on the list!" : "You're on the list!"}
          </h2>
          <p
            style={{
              fontSize: "var(--clay-body-md)",
              color: "var(--clay-body)",
              marginBottom: "var(--clay-spacing-xl)",
            }}
          >
            {isAlreadyRegistered
              ? "You're already on the waitlist. We'll get back to you soon!"
              : "We'll notify you when Kaplun is ready. Thanks for your interest!"}
          </p>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "var(--clay-primary)",
              color: "var(--clay-on-primary)",
              height: 44,
              padding: "12px 24px",
              borderRadius: "var(--clay-rounded-md)",
              fontSize: "var(--clay-button)",
              fontWeight: 600,
              fontFamily: '"Inter", sans-serif',
              border: "none",
              cursor: "pointer",
            }}
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(10, 10, 10, 0.5)",
        backdropFilter: "blur(8px)",
      }}
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
    >
      {/* eslint-disable-next-line jsx-a11y/no-static-element-interactions */}
      <div
        style={{
          background: "var(--clay-surface-card)",
          borderRadius: "var(--clay-rounded-xl)",
          padding: "var(--clay-spacing-2xl)",
          maxWidth: 440,
          width: "90%",
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <h2
          style={{
            fontSize: "var(--clay-title-lg)",
            fontWeight: 600,
            color: "var(--clay-ink)",
            marginBottom: "var(--clay-spacing-xs)",
            textAlign: "center",
          }}
        >
          Join the Waitlist
        </h2>
        <p
          style={{
            fontSize: "var(--clay-body-sm)",
            color: "var(--clay-muted)",
            marginBottom: "var(--clay-spacing-xl)",
            textAlign: "center",
          }}
        >
          Be the first to know when Kaplun launches.
        </p>

        <form onSubmit={handleSubmit}>
          <label
            htmlFor="waitlist-email"
            style={{
              display: "block",
              fontSize: "var(--clay-body-sm)",
              fontWeight: 500,
              color: "var(--clay-ink)",
              marginBottom: "var(--clay-spacing-xs)",
            }}
          >
            Email address
          </label>
          <input
            id="waitlist-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            style={{
              width: "100%",
              height: 44,
              padding: "12px 16px",
              borderRadius: "var(--clay-rounded-md)",
              border: "1px solid var(--clay-hairline)",
              fontSize: "var(--clay-body-md)",
              fontFamily: '"Inter", sans-serif',
              color: "var(--clay-ink)",
              background: "var(--clay-canvas)",
              outline: "none",
              boxSizing: "border-box",
              marginBottom: errors?.fields?.emailAddress
                ? "var(--clay-spacing-xs)"
                : "var(--clay-spacing-md)",
            }}
          />
          {errors?.fields?.emailAddress && (
            <p
              style={{
                fontSize: "var(--clay-body-sm)",
                color: "#dc2626",
                marginBottom: "var(--clay-spacing-md)",
              }}
            >
              {errors.fields.emailAddress.longMessage}
            </p>
          )}
          <button
            type="submit"
            disabled={fetchStatus === "fetching"}
            style={{
              width: "100%",
              height: 44,
              padding: "12px 20px",
              borderRadius: "var(--clay-rounded-md)",
              fontSize: "var(--clay-button)",
              fontWeight: 600,
              fontFamily: '"Inter", sans-serif',
              border: "none",
              cursor: fetchStatus === "fetching" ? "not-allowed" : "pointer",
              background: "var(--clay-primary)",
              color: "var(--clay-on-primary)",
              opacity: fetchStatus === "fetching" ? 0.7 : 1,
            }}
          >
            {fetchStatus === "fetching" ? "Joining..." : "Join Waitlist"}
          </button>
        </form>

        <button
          type="button"
          onClick={onClose}
          style={{
            display: "block",
            width: "100%",
            marginTop: "var(--clay-spacing-sm)",
            background: "none",
            border: "none",
            color: "var(--clay-muted)",
            fontSize: "var(--clay-body-sm)",
            cursor: "pointer",
            fontFamily: '"Inter", sans-serif',
          }}
        >
          Maybe later
        </button>
      </div>
    </div>
  );
}
