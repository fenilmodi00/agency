interface LogoProps {
  size?: number;
  className?: string;
}

export function Logo({ size = 28, className = "" }: LogoProps) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo.png"
      alt="Kaplun Logo"
      width={size}
      height={size}
      className={className}
      style={{
        display: "inline-block",
        verticalAlign: "middle",
        objectFit: "contain",
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "15%",
      }}
    />
  );
}
