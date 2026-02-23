import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials, req) {
        // 1. Llamamos a TU Backend (FastAPI) desde el servidor de Next.js
        // Usamos "http://api:8000" porque estamos dentro de la red Docker
        const res = await fetch("http://api:8000/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: credentials?.email,
            password: credentials?.password,
          }),
          headers: { "Content-Type": "application/json" },
        });

        const data = await res.json();

        // 2. Si el Backend dice "OK", dejamos pasar al usuario
        if (res.ok && data.user) {
          return {
            id: data.user.email, // <--- AGREGAMOS ESTO (Usamos el email como ID)
            name: data.user.name,
            email: data.user.email,
            role: data.user.role,
          };
        }

        // 3. Si no, rechazamos la entrada
        return null;
      }
    })
  ],
  pages: {
    signIn: "/login", // Si alguien intenta entrar sin permiso, lo mandamos aquí
  },
  callbacks: {
    async jwt({ token, user }) {
      return { ...token, ...user };
    },
    async session({ session, token }) {
      session.user = token as any;
      return session;
    },
  },
  secret: "secret-goalos-key-change-me", // En prod esto va en .env
});

export { handler as GET, handler as POST };