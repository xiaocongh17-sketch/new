import { describe, it, expect } from "vitest";
import { render, screen } from "../utils";
import { StatCard } from "@/components/StatCard";
import { Home } from "lucide-react";

describe("StatCard", () => {
  it("renders title, value and description", () => {
    render(
      <StatCard
        title="房源总数"
        value={42}
        icon={Home}
        description="全部房源"
      />
    );
    expect(screen.getByText("房源总数")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("全部房源")).toBeInTheDocument();
  });

  it("renders zero value", () => {
    render(
      <StatCard
        title="待审对话"
        value={0}
        icon={Home}
      />
    );
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders icon component", () => {
    render(
      <StatCard
        title="在租房源"
        value={8}
        icon={Home}
      />
    );
    expect(screen.getByText("在租房源")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });
});
