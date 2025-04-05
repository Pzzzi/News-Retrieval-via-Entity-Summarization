import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const EntityGraph = ({ entity, relatedEntities, links, onEntityClick }) => {
  const svgRef = useRef();

  const colorMap = {
    PERSON: "#1f77b4",
    ORGANIZATION: "#ff7f0e",
    LOCATION: "#2ca02c",
    DATE: "#d62728",
    MONEY: "#e377c2",
    EVENT: "#bcbd22",
    QUANTITY: "#17becf",
    DEFAULT: "#9467bd",
  };

  useEffect(() => {
    if (!relatedEntities.length) return;

    const width = 800;
    const height = 600;

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .style("background", "#f0f0f0");

    svg.selectAll("*").remove();

    const svgGroup = svg.append("g");

    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        svgGroup.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Prepare nodes data - only use relatedEntities (which includes the main entity)
    const nodes = relatedEntities.map(e => ({
      id: e.id,
      type: Array.isArray(e.type) ? e.type[0] : e.type,
      group: e.id === entity.id ? "main" : "related",
      radius: e.id === entity.id ? 12 : 8  // Larger radius for main entity
    }));

    // Prepare links data
    const linkData = links.map(link => ({
      source: link.source,
      target: link.target
    }));

    // Create a map of node degrees for sizing
    const nodeDegree = {};
    links.forEach(link => {
      nodeDegree[link.source] = (nodeDegree[link.source] || 0) + 1;
      nodeDegree[link.target] = (nodeDegree[link.target] || 0) + 1;
    });

    // Adjust node radius based on degree (except main entity)
    nodes.forEach(node => {
      if (nodeDegree[node.id] && node.id !== entity.id) {
        node.radius = Math.min(6 + nodeDegree[node.id] * 2, 15);
      }
    });

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(linkData).id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(d => d.group === "main" ? 0.5 : 0.05))
      .force("y", d3.forceY(height / 2).strength(d => d.group === "main" ? 0.5 : 0.05))
      .force("collision", d3.forceCollide().radius(d => d.radius + 5));

    // Draw links
    const link = svgGroup.selectAll(".link")
      .data(linkData)
      .enter().append("line")
      .attr("class", "link")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", d => {
        return (d.source === entity.id || d.target === entity.id) ? 2 : 1;
      });

    // Draw nodes with enhanced main entity styling
    const node = svgGroup.selectAll(".node")
      .data(nodes)
      .enter().append("circle")
      .attr("class", "node")
      .attr("r", d => d.radius)
      .attr("fill", d => {
        const type = Array.isArray(d.type) ? d.type[0] : d.type;
        return colorMap[type] || colorMap.DEFAULT;
      })
      .attr("stroke", d => d.group === "main" ? "#000" : "none")
      .attr("stroke-width", d => d.group === "main" ? 2 : 0)
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        if (d.id !== entity.id) {
          onEntityClick(d.id);
        }
      });

    // Tooltip
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("padding", "6px 10px")
      .style("background", "white")
      .style("border", "1px solid #ccc")
      .style("border-radius", "4px")
      .style("box-shadow", "0px 2px 8px rgba(0,0,0,0.15)")
      .style("pointer-events", "none")
      .style("opacity", 0);

    node
      .on("mouseover", (event, d) => {
        tooltip
          .html(`<strong>${d.id}</strong><br/><em>Type: ${Array.isArray(d.type) ? d.type.join(", ") : d.type || "N/A"}</em>`)
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 28}px`)
          .style("opacity", 1);
      })
      .on("mousemove", (event) => {
        tooltip
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 28}px`);
      })
      .on("mouseout", () => {
        tooltip.style("opacity", 0);
      });

    // Add labels with better positioning
    const text = svgGroup.selectAll(".label")
      .data(nodes)
      .enter().append("text")
      .attr("class", "label")
      .text(d => d.id)
      .attr("font-size", d => d.group === "main" ? "12px" : "10px")
      .attr("dx", d => d.radius + 2)
      .attr("dy", "0.35em")
      .style("pointer-events", "none")
      .style("font-weight", d => d.group === "main" ? "bold" : "normal");

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
        .attr("x", d => d.x + d.radius + 2)
        .attr("y", d => d.y);
    });

    return () => tooltip.remove();
  }, [entity, relatedEntities, links, onEntityClick]);

  return <svg ref={svgRef}></svg>;
};

export default EntityGraph;