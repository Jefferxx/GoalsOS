"use client";

import { signOut, useSession } from "next-auth/react";

export default function UserMenu() {
  const { data: session } = useSession();

  return (
    <div className="flex items-center gap-4">
      {session?.user && (
        <div className="hidden md:block text-right">
          <p className="text-xs text-slate-400 font-bold uppercase">Bienvenido</p>
          <p className="text-sm text-emerald-400 font-mono">{session.user.email}</p>
        </div>
      )}
      
      <button
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/50 px-4 py-2 rounded text-xs font-bold transition-all uppercase tracking-wider"
      >
        Cerrar Sesión 🛑
      </button>
    </div>
  );
}