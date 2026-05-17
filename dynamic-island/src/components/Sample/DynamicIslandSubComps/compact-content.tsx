import { motion } from "motion/react";
import type { SubComponentProps } from "../types";

const CompactContent = ({ content }: SubComponentProps) => {
  return (
    <motion.div
      key="compact"
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.85 }}
      transition={{ duration: 0.2 }}
      className="absolute inset-0 flex items-center justify-between px-3 gap-2"
    >
      {/* Left: icon + title */}
      <div className="flex items-center gap-2 min-w-0">
        {content.icon && <span className="text-white flex-shrink-0 text-base">{content.icon}</span>}
        <span className="text-white text-xs font-medium truncate">{content.title}</span>
      </div>

      {/* Right side slot */}
      {content.right && (
        <div className="flex-shrink-0 text-white/70 text-base">{content.right}</div>
      )}
    </motion.div>
  );
};

export default CompactContent;
