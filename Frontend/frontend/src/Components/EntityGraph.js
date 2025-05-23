import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import '../styles/EntityGraph.css';

const EntityGraph = ({ entity, relatedEntities, links, onEntityClick }) => {
  const svgRef = useRef();

  // Enhanced color palette with better contrast
  const colorMap = {
    PERSON: "#4e79a7",
    ORG: "#f28e2b",
    GPE: "#59a14f",
    DATE: "#e15759",
    MONEY: "#b07aa1",
    EVENT: "#edc948",
    QUANTITY: "#76b7b2",
    UNKNOWN: "#ff9da7",
  };

  useEffect(() => {
    if (!relatedEntities.length) return;

    const width = 1000;
    const height = 500;
    const padding = 20;

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .style("background", "#f8f9fa")
      .style("border-radius", "8px");

    svg.selectAll("*").remove();

    const svgGroup = svg.append("g");

    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        svgGroup.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Prepare nodes data
    const nodes = relatedEntities.map(e => ({
      id: e.id,
      type: Array.isArray(e.type) ? e.type[0] : e.type,
      group: e.id === entity.id ? "main" : "related",
      radius: e.id === entity.id ? 16 : 10  // More distinct size difference
    }));

  // Merge multiple relations for the same edge into one
  const mergedLinksMap = new Map();

  links.forEach(link => {
    const key = link.source < link.target
      ? `${link.source}|${link.target}`
      : `${link.target}|${link.source}`;

    if (!mergedLinksMap.has(key)) {
      mergedLinksMap.set(key, {
        source: link.source,
        target: link.target,
        relation: link.relation,  // just take the first relation
        confidence: link.confidence
      });
    }
  });

  const linkData = Array.from(mergedLinksMap.values());

    // Calculate node degrees for sizing
    const nodeDegree = {};
    links.forEach(link => {
      nodeDegree[link.source] = (nodeDegree[link.source] || 0) + 1;
      nodeDegree[link.target] = (nodeDegree[link.target] || 0) + 1;
    });

    // Adjust node radius based on degree
    nodes.forEach(node => {
      if (nodeDegree[node.id]) {
        node.radius = node.id === entity.id 
          ? 16 
          : Math.min(8 + nodeDegree[node.id] * 1.5, 14);
      }
    });

    // Improved force simulation parameters
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(linkData)
        .id(d => d.id)
        .distance(d => {
          // Increase distance for main entity connections
          return (d.source === entity.id || d.target === entity.id) ? 180 : 120;
        })
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(d => d.group === "main" ? 0.5 : 0.02))
      .force("y", d3.forceY(height / 2).strength(d => d.group === "main" ? 0.5 : 0.02))
      .force("collision", d3.forceCollide().radius(d => d.radius + 8));

    // Draw links with better styling
    const link = svgGroup.selectAll(".link")
      .data(linkData)
      .enter().append("line")
      .attr("class", "link")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", d => {
        return (d.source === entity.id || d.target === entity.id) ? 2.5 : 1.5;
      });

    // Add link labels (relationship types)
  const linkLabels = svgGroup.selectAll(".link-label")
    .data(linkData)
    .enter().append("text")
    .attr("class", "link-label")
    .attr("font-size", "10px")
    .attr("fill", "#757475") // Darker color for better contrast
    .style("pointer-events", "none")
    .style("font-weight", "bold") // Make relationship text bold
    .style("font-style", "italic") // Optional: italicize relationships
    .style("text-shadow", "0 1px 2px white") // Add subtle text shadow for readability
    .text(d => {
      // Simplify some of the relation types for display
      if (d.relation === "Entity-Destination(e2,e1)") return "→ Destination";
      if (d.relation === "Instrument-Agency(e2,e1)") return "← Agency";
      if (d.relation === "Message-Topic(e1,e2)") return "Topic →";
      return d.relation;
    });

    // Draw nodes with enhanced styling
    const node = svgGroup.selectAll(".node")
      .data(nodes)
      .enter().append("circle")
      .attr("class", "node")
      .attr("r", d => d.radius)
      .attr("fill", d => {
        const type = Array.isArray(d.type) ? d.type[0] : d.type;
        return colorMap[type] || colorMap.UNKNOWN;
      })
      .attr("stroke", d => d.group === "main" ? "#333" : "none")
      .attr("stroke-width", d => d.group === "main" ? 2.5 : 0)
      .style("cursor", "pointer")
      .style("opacity", 0.9)
      .on("click", (event, d) => {
        if (d.id !== entity.id) {
          onEntityClick(d.id);
        }
      });

    // Improved tooltip
    const tooltip = d3.select("body")
      .append("div")
      .attr("class", "entity-tooltip")
      .style("position", "absolute")
      .style("padding", "8px 12px")
      .style("background", "rgba(255, 255, 255, 0.95)")
      .style("border", "1px solid #ddd")
      .style("border-radius", "6px")
      .style("box-shadow", "0 2px 12px rgba(0,0,0,0.15)")
      .style("pointer-events", "none")
      .style("opacity", 0)
      .style("font-family", "sans-serif")
      .style("font-size", "13px")
      .style("z-index", "1000");

    node
      .on("mouseover", (event, d) => {
        tooltip
          .html(`
            <div style="margin-bottom: 4px; font-weight: bold; color: ${colorMap[Array.isArray(d.type) ? d.type[0] : d.type] || colorMap.UNKNOWN}">
              ${d.id}
            </div>
            <div style="font-size: 0.9em; color: #666">
              Type: ${Array.isArray(d.type) ? d.type.join(", ") : d.type || "N/A"}
            </div>
          `)
          .style("left", `${event.pageX + 15}px`)
          .style("top", `${event.pageY - 15}px`)
          .style("opacity", 1);
        
        // Highlight connected nodes and links
        svgGroup.selectAll(".link")
          .style("stroke-opacity", l => 
            (l.source.id === d.id || l.target.id === d.id) ? 0.8 : 0.2);
        
        svgGroup.selectAll(".node")
          .style("opacity", n => 
            n.id === d.id || linkData.some(l => 
              (l.source.id === d.id && l.target.id === n.id) || 
              (l.target.id === d.id && l.source.id === n.id)
            ) ? 1 : 0.3);
      })
      .on("mousemove", (event) => {
        tooltip
          .style("left", `${event.pageX + 15}px`)
          .style("top", `${event.pageY - 15}px`);
      })
      .on("mouseout", () => {
        tooltip.style("opacity", 0);
        // Reset all opacities
        svgGroup.selectAll(".link").style("stroke-opacity", 0.4);
        svgGroup.selectAll(".node").style("opacity", 0.9);
      });

    // Improved labels with background for better readability
    const labels = svgGroup.selectAll(".label")
      .data(nodes)
      .enter().append("g")
      .attr("class", "label")

    // Add text centered on the node
    labels.append("text")
      .text(d => d.id)
      .attr("font-size", d => d.group === "main" ? "10px" : "8px") // Smaller font
      .attr("text-anchor", "middle") // Center horizontally
      .attr("dy", "0.35em") // Center vertically
      .style("pointer-events", "none")
      .style("font-weight", "bold")
      .style("fill", "#000") // White text for better contrast
      .style("font-family", "Arial, sans-serif")
      .style("text-shadow", "0 1px 2px rgba(0,0,0,0.5)"); // Add shadow for readability

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      // Update link label positions
      linkLabels
        .attr("x", d => (d.source.x + d.target.x) / 2)
        .attr("y", d => (d.source.y + d.target.y) / 2);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      // Update label positions to center on nodes
      labels
        .attr("transform", d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
      tooltip.remove();
    };
  }, [entity, relatedEntities, links, onEntityClick]);

  return <svg ref={svgRef}></svg>;
};

export default EntityGraph;