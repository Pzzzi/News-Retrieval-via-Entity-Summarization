import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const EntityGraph = ({ entity, relatedEntities, links, onEntityClick }) => {
  const svgRef = useRef();

  // Comprehensive color palette matching the other components
  const colorMap = {
    PERSON: "#4F46E5",      // Modern indigo
    NORP: "#7C3AED",        // Rich purple
    FAC: "#F59E0B",         // Warm amber
    ORG: "#DC2626",         // Strong red
    GPE: "#059669",         // Forest green
    LOC: "#0D9488",         // Teal
    PRODUCT: "#0891B2",     // Deep cyan
    EVENT: "#E11D48",       // Rose red
    WORK_OF_ART: "#C026D3", // Magenta
    LAW: "#7C2D12",         // Brown
    LANGUAGE: "#0284C7",    // Blue
    DATE: "#CA8A04",        // Gold
    TIME: "#EA580C",        // Orange
    PERCENT: "#65A30D",     // Lime
    MONEY: "#0F766E",       // Dark teal
    QUANTITY: "#BE185D",    // Pink
    ORDINAL: "#BE123C",     // Deep rose
    CARDINAL: "#D97706",    // Amber
    UNKNOWN: "#6B7280"      // Neutral gray
  };

  // Lighter versions for hover effects
  const lightColorMap = {
    PERSON: "#8B5CF6",
    NORP: "#A855F7",
    FAC: "#FBBF24",
    ORG: "#F87171",
    GPE: "#34D399",
    LOC: "#2DD4BF",
    PRODUCT: "#22D3EE",
    EVENT: "#FB7185",
    WORK_OF_ART: "#E879F9",
    LAW: "#A78BFA",
    LANGUAGE: "#38BDF8",
    DATE: "#FCD34D",
    TIME: "#FDBA74",
    PERCENT: "#A3E635",
    MONEY: "#5EEAD4",
    QUANTITY: "#F472B6",
    ORDINAL: "#FDA4AF",
    CARDINAL: "#FBBF24",
    UNKNOWN: "#9CA3AF"
  };

  // Relationship label mapping
  const relationLabels = {
    "Cause-Effect(e1,e2)": "Cause →",
    "Cause-Effect(e2,e1)": "← Effect",
    "Instrument-Agency(e1,e2)": "Tool →",
    "Instrument-Agency(e2,e1)": "← User",
    "Product-Producer(e1,e2)": "Product →",
    "Product-Producer(e2,e1)": "← Maker",
    "Content-Container(e1,e2)": "Inside →",
    "Content-Container(e2,e1)": "← Contains",
    "Entity-Origin(e1,e2)": "Origin →",
    "Entity-Origin(e2,e1)": "← From",
    "Entity-Destination(e1,e2)": "→ Destination",
    "Entity-Destination(e2,e1)": "Target ←",
    "Component-Whole(e1,e2)": "Part →",
    "Component-Whole(e2,e1)": "← Whole",
    "Member-Collection(e1,e2)": "Member →",
    "Member-Collection(e2,e1)": "← Group",
    "Message-Topic(e1,e2)": "Topic →",
    "Message-Topic(e2,e1)": "← About",
    "Other": "─ Other"
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
          relation: link.relation,
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

    // Add link labels (relationship types) with our new standardized labels
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
      .text(d => relationLabels[d.relation] || d.relation);

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

  return (
    <div style={{
      padding: '20px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: '20px',
      margin: '10px'
    }}>
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default EntityGraph;