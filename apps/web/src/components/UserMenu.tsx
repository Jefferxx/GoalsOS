"use client";

import { signOut, useSession } from "next-auth/react";
import { LogOut } from "lucide-react";

export default function UserMenu() {
  const { data: session } = useSession();

  return (
    <div className="flex items-center gap-4">
      {session?.user && (
        <div className="hidden md:block text-right">
          <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Bienvenido</p>
          <p className="text-sm text-zinc-300 font-mono">{session.user.email}</p>
        </div>
      )}

      <button
        onClick={() => signOut({ callbackUrl: "/login" })}
        className="flex items-center gap-1.5 text-zinc-500 hover:text-red-500 px-3 py-2 rounded text-xs font-bold transition-colors uppercase tracking-wider cursor-pointer"
      >
        <LogOut size={14} />
        Cerrar Sesión
      </button>
    </div>
  );
}
