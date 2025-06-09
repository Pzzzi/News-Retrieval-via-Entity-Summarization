import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import '../styles/EntityGraph.css';

const EntityGraph = ({ entity, relatedEntities, links, onEntityClick }) => {
  const svgRef = useRef();

  // Comprehensive color palette matching the other components
  const colorMap = {
    PERSON: "#3B82F6",      // blue-600
    NORP: "#8B5CF6",        // purple-600
    FAC: "#F59E0B",         // amber-600
    ORG: "#F43F5E",         // indigo-600
    GPE: "#10B981",         // green-600
    LOC: "#059669",         // emerald-600
    PRODUCT: "#06B6D4",     // cyan-600
    EVENT: "#EF4444",       // red-600
    WORK_OF_ART: "#D946EF", // fuchsia-600
    LAW: "#7C3AED",         // violet-600
    LANGUAGE: "#0EA5E9",    // sky-600
    DATE: "#EAB308",        // yellow-600
    TIME: "#F97316",        // orange-600
    PERCENT: "#84CC16",     // lime-600
    MONEY: "#14B8A6",       // teal-600
    QUANTITY: "#EC4899",    // pink-600
    ORDINAL: "#6366F1",     // rose-600
    CARDINAL: "#F59E0B",    // amber-600 (same as FAC)
    UNKNOWN: "#9CA3AF"      // gray-400
  };

  // Lighter versions for hover effects
  const lightColorMap = {
    PERSON: "#93C5FD",      // blue-300
    NORP: "#C4B5FD",        // purple-300
    FAC: "#FCD34D",         // amber-300
    ORG: "#A5B4FC",         // indigo-300
    GPE: "#6EE7B7",         // green-300
    LOC: "#6EE7B7",         // emerald-300
    PRODUCT: "#67E8F9",     // cyan-300
    EVENT: "#FCA5A5",       // red-300
    WORK_OF_ART: "#F0ABFC", // fuchsia-300
    LAW: "#C4B5FD",         // violet-300
    LANGUAGE: "#7DD3FC",    // sky-300
    DATE: "#FDE047",        // yellow-300
    TIME: "#FDBA74",        // orange-300
    PERCENT: "#BEF264",     // lime-300
    MONEY: "#5EEAD4",       // teal-300
    QUANTITY: "#F9A8D4",    // pink-300
    ORDINAL: "#FDA4AF",     // rose-300
    CARDINAL: "#FCD34D",    // amber-300 (same as FAC)
    UNKNOWN: "#D1D5DB"      // gray-300
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
      radius: e.id === entity.id ? 20 : 12  // More distinct size difference
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
          ? 20
          : Math.min(10 + nodeDegree[node.id] * 1.5, 16);
      }
    });

    // Improved force simulation parameters
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(linkData)
        .id(d => d.id)
        .distance(d => {
          // Main entity connections get more distance
          if (d.source.id === entity.id || d.target.id === entity.id) {
            return 180;
          }
          // Connections between highly connected nodes get more distance
          const sourceDegree = nodeDegree[d.source.id] || 1;
          const targetDegree = nodeDegree[d.target.id] || 1;
          return 80 + Math.min(sourceDegree, targetDegree) * 10;
        })
      )
      .force("charge", d3.forceManyBody()
        .strength(d => {
          // Scale repulsion by node degree
          const degree = nodeDegree[d.id] || 1;
          return -200 / Math.sqrt(degree + 1);
        })
      )
      .force("x", d3.forceX(width / 2)
        .strength(d => d.id === entity.id ? 0.1 : 0.01)
      )
      .force("y", d3.forceY(height / 2)
        .strength(d => d.id === entity.id ? 0.1 : 0.01)
      )
      .force("collision", d3.forceCollide()
        .radius(d => d.radius + 5)
        .strength(0.8)
      );

    // Initialize positions to prevent circular clustering
    nodes.forEach((node, i) => {
      if (node.id === entity.id) {
        node.x = width / 2;
        node.y = height / 2;
        node.fx = width / 2; // Fixed position for main entity
        node.fy = height / 2;
      } else {
        const angle = Math.random() * Math.PI * 2;
        const radius = 100 + Math.random() * 50;
        node.x = width / 2 + radius * Math.cos(angle);
        node.y = height / 2 + radius * Math.sin(angle);
      }
    });

    // Start with higher alpha to get things moving
    simulation.alpha(1).restart();

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
      .attr("fill", "#757475")
      .style("pointer-events", "none")
      .style("font-weight", "bold")
      .style("font-style", "italic")
      .style("text-shadow", "0 1px 2px white")
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
      .attr("stroke", d => d.group === "main" ? "#1F2937" : "none") // gray-800 for main entity
      .attr("stroke-width", d => d.group === "main" ? 3 : 0)
      .style("cursor", "pointer")
      .style("opacity", 0.9)
      .on("click", (event, d) => {
        if (d.id !== entity.id) {
          // Find the full entity data from relatedEntities
          const clickedEntity = relatedEntities.find(e => e.id === d.id);
          if (clickedEntity) {
            onEntityClick(clickedEntity);  // Pass the full entity object
          }
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
        const type = Array.isArray(d.type) ? d.type[0] : d.type;
        const color = colorMap[type] || colorMap.UNKNOWN;

        tooltip
          .html(`
            <div style="margin-bottom: 4px; font-weight: bold; color: ${color}">
              ${d.id}
            </div>
            <div style="font-size: 0.9em; color: #666">
              Type: ${Array.isArray(d.type) ? d.type.join(", ") : d.type || "N/A"}
            </div>
            ${d.group === "main" ? `<div style="margin-top: 4px; font-size: 0.8em; color: #999">(Main Entity)</div>` : ''}
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
            ) ? 1 : 0.3)
          .attr("fill", n => {
            if (n.id === d.id) {
              const type = Array.isArray(n.type) ? n.type[0] : n.type;
              return lightColorMap[type] || lightColorMap.UNKNOWN;
            }
            const type = Array.isArray(n.type) ? n.type[0] : n.type;
            return colorMap[type] || colorMap.UNKNOWN;
          });
      })
      .on("mousemove", (event) => {
        tooltip
          .style("left", `${event.pageX + 15}px`)
          .style("top", `${event.pageY - 15}px`);
      })
      .on("mouseout", () => {
        tooltip.style("opacity", 0);
        // Reset all opacities and colors
        svgGroup.selectAll(".link").style("stroke-opacity", 0.4);
        svgGroup.selectAll(".node")
          .style("opacity", 0.9)
          .attr("fill", d => {
            const type = Array.isArray(d.type) ? d.type[0] : d.type;
            return colorMap[type] || colorMap.UNKNOWN;
          });
      });

    // Improved labels with better readability
    const labels = svgGroup.selectAll(".label")
      .data(nodes)
      .enter().append("g")
      .attr("class", "label")

    // Add text centered on the node
    labels.append("text")
      .text(d => d.id)
      .attr("font-size", d => d.group === "main" ? "11px" : "9px")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("pointer-events", "none")
      .style("font-weight", "bold")
      .style("fill", "#111827") // gray-900
      .style("font-family", "Arial, sans-serif")
      .style("text-shadow", "0 1px 2px rgba(255,255,255,0.7)");

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