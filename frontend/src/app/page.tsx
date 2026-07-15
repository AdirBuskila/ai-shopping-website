export default function Home() {
  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-2xl bg-brand-gradient px-8 py-16 text-white shadow-lg">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
          Electronics, with an assistant that actually knows the shelf.
        </h1>
        <p className="mt-4 max-w-xl text-lg text-white/80">
          Browse the catalog, search by anything, and ask the AI what fits your budget.
        </p>
      </section>
      <p className="text-center text-ink-muted">Storefront coming together — product grid next.</p>
    </div>
  );
}
