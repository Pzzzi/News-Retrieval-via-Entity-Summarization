import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const EntityGraph = ({ entity, relatedEntities, onEntityClick }) => {
  const svgRef = useRef();

  // Entity color mapping based on types
  const colorMap = {
    PERSON: "#1f77b4",       // Blue
    ORGANIZATION: "#ff7f0e", // Orange
    LOCATION: "#2ca02c",     // Green
    DATE: "#d62728",         // Red
    MONEY: "#e377c2",        // Pink
    EVENT: "#bcbd22",        // Yellow-Green
    QUANTITY: "#17becf",     // Cyan
    DEFAULT: "#9467bd",      // Purple
  };

  useEffect(() => {
    if (!relatedEntities.length) return;

    const width = 600;
    const height = 400;

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .style("background", "#f0f0f0");

    svg.selectAll("*").remove();  // Clear existing graph

    // Nodes: include entity and relatedEntities
    const nodes = [{ id: entity.id, type: entity.type, group: "main" }, ...relatedEntities];

    // Links: all related entities connect to the main entity
    const links = relatedEntities.map(e => ({ source: entity.id, target: e.id }));

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Links (lines)
    const link = svg.selectAll(".link")
      .data(links)
      .enter().append("line")
      .attr("class", "link")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 1.5);

    // Nodes (circles)
    const node = svg.selectAll(".node")
      .data(nodes)
      .enter().append("circle")
      .attr("class", "node")
      .attr("r", d => (d.group === "main" ? 10 : 6))
      .attr("fill", d => colorMap[d.type] || colorMap.DEFAULT)  // Color coding
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        if (d.id !== entity.id) {
          onEntityClick(d.id);
        }
      });

    // Labels (text)
    const text = svg.selectAll(".text")
      .data(nodes)
      .enter().append("text")
      .text(d => d.id)
      .attr("font-size", "12px")
      .attr("dx", 12)
      .attr("dy", 3);

    // Simulation updates on each tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      text
        .attr("x", d => d.x + 12)
        .attr("y", d => d.y + 3);
    });
  }, [entity, relatedEntities, onEntityClick]);

  return <svg ref={svgRef}></svg>;
};

export default EntityGraph;


