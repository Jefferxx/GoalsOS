export { default } from "next-auth/middleware";

// Aquí definimos qué rutas están PROHIBIDAS para extraños
export const config = {
  matcher: ["/", "/match/:path*"]
};