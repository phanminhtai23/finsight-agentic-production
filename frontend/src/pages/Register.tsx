import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthShell } from "../components/AuthShell";
import { GoogleSignIn } from "../components/GoogleSignIn";
import { Button, Input } from "../components/ui";
import { api } from "../lib/api";

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Client-side guards before hitting the API.
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const { data } = await api.post("/auth/register", {
        email,
        password,
        full_name: fullName || null,
      });
      // Email delivery not configured/available on the server → expose the manual link
      // instead of silently verifying, so verification stays an explicit step.
      if (data.verification_token) setDevToken(data.verification_token);
      setSent(true);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <AuthShell title="Check your email" subtitle="We sent you a verification link.">
        <p className="text-sm text-neutral-500">
          Open the link in your inbox to verify your account, then sign in. The link expires
          after a while — request a new one by registering again if it does.
        </p>
        {devToken && (
          <div className="mt-4 rounded-lg border border-amber-300/60 bg-amber-50 p-3 text-xs dark:border-amber-500/30 dark:bg-amber-500/10">
            <p className="mb-2 text-amber-700 dark:text-amber-400">
              Email delivery isn’t configured on this server, so no message was sent. You can
              verify manually:
            </p>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => navigate(`/verify-email?token=${devToken}`)}
            >
              Verify now
            </Button>
          </div>
        )}
        <Link to="/login">
          <Button className="mt-4 w-full">Back to sign in</Button>
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Create your account" subtitle="Start researching in minutes.">
      <form onSubmit={submit} className="space-y-3">
        <Input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <Input
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          type="password"
          placeholder="Password (min 8 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        <Input
          type="password"
          placeholder="Confirm password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          minLength={8}
          required
          aria-invalid={confirm.length > 0 && password !== confirm}
        />
        {confirm.length > 0 && password !== confirm && (
          <p className="text-xs text-amber-600">Passwords don’t match yet.</p>
        )}
        {error && <p className="text-sm text-red-500">{error}</p>}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </Button>
      </form>
      <GoogleSignIn />
      <p className="mt-4 text-center text-sm text-neutral-500">
        Already have an account?{" "}
        <Link to="/login" className="text-indigo-600 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
