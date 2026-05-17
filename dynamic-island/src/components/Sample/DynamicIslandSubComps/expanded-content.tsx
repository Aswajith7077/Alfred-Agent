import { motion } from "motion/react";
import type { SubComponentProps } from "../types";

const ExpandedContent = ({ content }: SubComponentProps) => {
  return (
    <motion.div
      key="expanded"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      transition={{ duration: 0.22 }}
      className="absolute inset-0 flex items-center px-4 gap-3"
    >
      {content.icon && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-white text-lg">
          {content.icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm font-semibold truncate leading-tight">{content.title}</p>
        {content.subtitle && (
          <p className="text-white/50 text-xs truncate mt-0.5">{content.subtitle}</p>
        )}
      </div>
      {content.right && <div className="flex-shrink-0">{content.right}</div>}
    </motion.div>
  );
};

export default ExpandedContent;
