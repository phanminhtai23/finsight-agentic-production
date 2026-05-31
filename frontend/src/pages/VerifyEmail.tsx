import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AuthShell } from "../components/AuthShell";
import { Button, Spinner } from "../components/ui";
import { api } from "../lib/api";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const [status, setStatus] = useState<"pending" | "ok" | "error">("pending");

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setStatus("error");
      return;
    }
    api
      .get(`/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, [params]);

  return (
    <AuthShell title="Email verification">
      {status === "pending" && (
        <div className="flex items-center gap-3 text-sm text-neutral-500">
          <Spinner /> Verifying…
        </div>
      )}
      {status === "ok" && (
        <>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Your email is verified. You can sign in now.
          </p>
          <Link to="/login">
            <Button className="mt-4 w-full">Continue to sign in</Button>
          </Link>
        </>
      )}
      {status === "error" && (
        <>
          <p className="text-sm text-red-500">This verification link is invalid or expired.</p>
          <Link to="/register">
            <Button variant="outline" className="mt-4 w-full">
              Register again
            </Button>
          </Link>
        </>
      )}
    </AuthShell>
  );
}
