"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { LogIn, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Usamos la función signIn de NextAuth
    const result = await signIn("credentials", {
      email,
      password,
      redirect: false, // Manejamos la redirección manualmente
    });

    if (result?.error) {
      setError("Credenciales inválidas. Acceso denegado.");
    } else {
      router.push("/"); // ¡Adentro!
      router.refresh();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-zinc-50">GoalOS</h1>
          <p className="text-zinc-500 text-sm mt-2 tracking-widest uppercase">Sistema de Acceso Restringido</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center gap-2 text-red-500 text-sm justify-center">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <div>
            <label className="block text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Email Corporativo</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-transparent border-b border-zinc-800 p-3 text-zinc-50 focus:border-emerald-500 outline-none transition-colors"
              placeholder="admin@goalos.com"
              required
            />
          </div>

          <div>
            <label className="block text-zinc-500 text-xs font-bold uppercase tracking-widest mb-2">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-transparent border-b border-zinc-800 p-3 text-zinc-50 focus:border-emerald-500 outline-none transition-colors"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold py-3 rounded transition-colors"
          >
            <LogIn size={16} />
            Iniciar Sesión
          </button>
        </form>
      </div>
    </div>
  );
}
