import { useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { api, formatBytes } from "../lib/api";
import { TierBadge } from "./TierBadge";
import { Button } from "./ui";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 text-sm">
      <span className="text-neutral-500">{label}</span>
      <span className="font-medium">{children}</span>
    </div>
  );
}

export function ProfileModal({ onClose }: { onClose: () => void }) {
  const { user, logout, refreshUser } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);
  if (!user) return null;

  async function uploadAvatar(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    await api.post("/auth/me/avatar", fd);
    await refreshUser();
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-sm rounded-2xl border border-neutral-200 bg-white p-6 shadow-xl dark:border-neutral-800 dark:bg-neutral-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col items-center text-center">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => e.target.files?.[0] && uploadAvatar(e.target.files[0])}
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="group relative"
            title="Change avatar"
          >
            {user.avatar_url ? (
              <img src={user.avatar_url} className="h-20 w-20 rounded-full object-cover" />
            ) : (
              <div className="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-2xl font-bold text-white">
                {(user.full_name ?? user.email)[0]?.toUpperCase()}
              </div>
            )}
            <span className="absolute inset-0 grid place-items-center rounded-full bg-black/40 text-xs text-white opacity-0 transition group-hover:opacity-100">
              Change
            </span>
          </button>
          <div className="mt-3 flex items-center gap-2">
            <h2 className="text-lg font-semibold">{user.full_name ?? "Account"}</h2>
            <TierBadge tier={user.tier} />
          </div>
          <p className="text-sm text-neutral-500">{user.email}</p>
        </div>

        <div className="mt-5 divide-y divide-neutral-200 dark:divide-neutral-800">
          <Row label="Plan">
            <TierBadge tier={user.tier} />
          </Row>
          <Row label="Email">{user.is_verified ? "Verified ✓" : "Unverified"}</Row>
          <Row label="Sign-in">{user.auth_provider}</Row>
          <Row label="Storage used">{formatBytes(user.storage_used_bytes)}</Row>
          <Row label="Member since">{new Date(user.created_at).toLocaleDateString()}</Row>
        </div>

        <div className="mt-5 flex gap-2">
          <Button variant="outline" className="flex-1" onClick={() => fileRef.current?.click()}>
            Change avatar
          </Button>
          <Button
            variant="outline"
            className="flex-1 text-red-600"
            onClick={() => {
              logout();
              onClose();
            }}
          >
            Sign out
          </Button>
        </div>
      </div>
    </div>
  );
}
