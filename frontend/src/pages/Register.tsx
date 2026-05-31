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
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post("/auth/register", {
        email,
        password,
        full_name: fullName || null,
      });
      // Dev fallback: the backend returns the verification token when email is not configured.
      if (data.verification_token) {
        navigate(`/verify-email?token=${data.verification_token}`);
      } else {
        setSent(true);
      }
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
          Open the link in your inbox to verify your account, then sign in.
        </p>
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
