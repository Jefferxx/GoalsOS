"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";

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
      setError("❌ Credenciales inválidas. Acceso denegado.");
    } else {
      router.push("/"); // ¡Adentro!
      router.refresh();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
            GoalOS Enterprise
          </h1>
          <p className="text-slate-400 text-sm mt-2">Sistema de Acceso Restringido</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <label className="block text-slate-400 text-xs font-bold uppercase mb-2">Email Corporativo</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded p-3 text-white focus:border-emerald-500 outline-none transition-colors"
              placeholder="admin@goalos.com"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 text-xs font-bold uppercase mb-2">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded p-3 text-white focus:border-emerald-500 outline-none transition-colors"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded transition-all shadow-lg shadow-emerald-900/50"
          >
            Iniciar Sesión 🔐
          </button>
        </form>
      </div>
    </div>
  );
}